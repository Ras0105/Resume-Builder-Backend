# app/routers/webhooks.py
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import get_settings
from app.database import get_db
from app.models import Order, OrderStatus, WebhookEvent
from app.services.pdf_pipeline import generate_and_deliver_pdf

router = APIRouter(prefix="/api/webhook", tags=["webhooks"])
settings = get_settings()


def _verify_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Razorpay signs the raw request body with your webhook secret using
    HMAC-SHA256. This MUST run on the raw bytes, before any JSON parsing —
    re-serializing a parsed payload can produce different bytes (key
    ordering, whitespace) and silently break verification, or worse,
    make it accidentally always pass.
    """
    if not signature_header:
        return False

    expected = hmac.new(
        key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # constant-time comparison — a plain == leaks timing info an attacker
    # could theoretically use to brute-force the signature byte by byte.
    return hmac.compare_digest(expected, signature_header)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    signature_header = request.headers.get("X-Razorpay-Signature", "")

    signature_valid = _verify_signature(raw_body, signature_header)

    # Parse for logging purposes regardless of validity — but nothing
    # gets acted on unless signature_valid is True.
    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError:
        parsed = {}

    event_type = parsed.get("event", "unknown")
    payment_entity = parsed.get("payload", {}).get("payment", {}).get("entity", {})
    razorpay_event_id = request.headers.get("X-Razorpay-Event-Id")
    razorpay_order_id = payment_entity.get("order_id")

    # ---- Reject invalid signatures outright ----
    if not signature_valid:
        db.add(WebhookEvent(
            id=str(uuid.uuid4()),
            order_id=None,
            razorpay_event_id=razorpay_event_id,
            event_type=event_type,
            signature_valid=False,
            raw_payload=raw_body.decode("utf-8", errors="replace"),
        ))
        db.commit()
        # 400, not 401/403 — don't hint at what would make it valid
        raise HTTPException(status_code=400, detail="Invalid signature")

    # ---- Idempotency: Razorpay retries webhooks; don't double-process ----
    if razorpay_event_id:
        existing = db.scalar(
            select(WebhookEvent).where(WebhookEvent.razorpay_event_id == razorpay_event_id)
        )
        if existing is not None:
            return {"status": "already_processed"}

    order = None
    if razorpay_order_id:
        order = db.scalar(
            select(Order).where(Order.razorpay_order_id == razorpay_order_id)
        )

    db.add(WebhookEvent(
        id=str(uuid.uuid4()),
        order_id=order.id if order else None,
        razorpay_event_id=razorpay_event_id,
        event_type=event_type,
        signature_valid=True,
        raw_payload=raw_body.decode("utf-8", errors="replace"),
    ))

    if order is None:
        # Signature was valid but we don't recognize this order — log and
        # move on rather than 500ing, so Razorpay doesn't retry forever.
        db.commit()
        return {"status": "order_not_found"}

    # ---- Only react to the events that mean "money has actually landed" ----
    if event_type == "payment.captured" and order.status == OrderStatus.PENDING:
        order.status = OrderStatus.PAID
        order.razorpay_payment_id = payment_entity.get("id")
        order.paid_at = datetime.now(timezone.utc)
        db.commit()

        # Kick off PDF generation + email after responding — Razorpay expects
        # a fast 2xx response and will retry on timeout, which would otherwise
        # trigger duplicate PDF generation on a slow render.
        background_tasks.add_task(generate_and_deliver_pdf, order.id)

    elif event_type == "payment.failed" and order.status == OrderStatus.PENDING:
        order.status = OrderStatus.FAILED
        db.commit()

    else:
        db.commit()

    return {"status": "ok"}