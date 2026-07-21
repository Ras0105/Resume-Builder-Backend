# app/services/payment.py
import razorpay

from app.config import get_settings

settings = get_settings()

_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
_client.set_app_details({"title": "ResumeDraft", "version": "1.0"})


class PaymentOrderError(Exception):
    """Raised when Razorpay fails to create an order."""
    pass


def create_razorpay_order(amount_paise: int, currency: str, receipt: str) -> dict:
    """
    Creates a Razorpay order for the given amount. This is called once,
    right after your own Order row is created — the returned order id is
    what the frontend passes into Razorpay's checkout widget.

    Note: this does NOT confirm payment. It just registers the intent to
    be paid. Confirmation only ever comes from the webhook.
    """
    try:
        return _client.order.create({
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,          # your internal Order.id, for cross-referencing
            "payment_capture": 1,        # auto-capture on successful payment
        })
    except razorpay.errors.BadRequestError as exc:
        raise PaymentOrderError(f"Razorpay rejected order creation: {exc}") from exc
    except Exception as exc:
        raise PaymentOrderError(f"Unexpected error creating Razorpay order: {exc}") from exc


def fetch_payment(payment_id: str) -> dict:
    """
    Optional reconciliation helper — fetches a payment's current state
    directly from Razorpay's API. Useful for a periodic job that double-
    checks orders stuck in PENDING in case a webhook was ever missed
    entirely (rare, but webhooks aren't 100% guaranteed delivery).
    """
    try:
        return _client.payment.fetch(payment_id)
    except Exception as exc:
        raise PaymentOrderError(f"Could not fetch payment {payment_id}: {exc}") from exc


def refund_payment(payment_id: str, amount_paise: int | None = None) -> dict:
    """
    Issues a refund — full refund if amount_paise is omitted, partial
    otherwise. Called manually from an admin action, not automatically,
    since refund decisions need a human in the loop.
    """
    payload = {}
    if amount_paise is not None:
        payload["amount"] = amount_paise

    try:
        return _client.payment.refund(payment_id, payload)
    except Exception as exc:
        raise PaymentOrderError(f"Could not refund payment {payment_id}: {exc}") from exc