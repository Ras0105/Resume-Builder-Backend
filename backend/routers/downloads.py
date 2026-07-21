# app/routers/downloads.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models import GeneratedPdf, Order, OrderStatus
from app.services.storage import get_presigned_download_url

router = APIRouter(prefix="/api/download", tags=["downloads"])

# Hard cap independent of expiry — stops a leaked link from being reused
# indefinitely even if someone extends their own clock or the row's TTL
# check has an edge case.
MAX_DOWNLOADS_PER_LINK = 5


@router.get("/{token}")
def download_resume(token: str, db: Session = Depends(get_db)):
    """
    Resolves a one-time signed download token to the actual PDF.
    The token itself (GeneratedPdf.download_token) is a long random
    string generated at PDF-creation time — this endpoint never
    accepts an order_id or pdf_id directly, only the opaque token,
    so guessing or enumerating IDs gets you nothing.
    """
    pdf = db.scalar(
        select(GeneratedPdf).where(GeneratedPdf.download_token == token)
    )

    if pdf is None:
        # Same response whether the token is malformed, unknown, or
        # from a different environment — don't leak which case it is.
        raise HTTPException(status_code=404, detail="Download link not found")

    order = db.get(Order, pdf.order_id)
    if order is None or order.status != OrderStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Download link not found")

    now = datetime.now(timezone.utc)
    if pdf.token_expires_at < now:
        raise HTTPException(
            status_code=410,
            detail="This download link has expired. Check your email for a fresh copy, or contact support.",
        )

    if pdf.download_count >= MAX_DOWNLOADS_PER_LINK:
        raise HTTPException(
            status_code=410,
            detail="This download link has already been used the maximum number of times.",
        )

    # Generate a short-lived presigned URL to the actual object rather than
    # streaming the file through this endpoint — cheaper, and the storage
    # provider's own URL expiry gives a second layer of time-boxing.
    presigned_url = get_presigned_download_url(pdf.storage_key, expires_in_seconds=120)

    pdf.download_count += 1
    db.commit()

    return RedirectResponse(url=presigned_url, status_code=307)