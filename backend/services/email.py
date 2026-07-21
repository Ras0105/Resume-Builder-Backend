# app/services/email.py
import resend

from app.config import get_settings

settings = get_settings()
resend.api_key = settings.EMAIL_API_KEY


class EmailDeliveryError(Exception):
    """Raised when the email provider fails to accept the send request."""
    pass


def send_resume_ready_email(
    to_email: str,
    customer_name: str,
    download_url: str,
    expires_in_minutes: int,
) -> None:
    """
    Sends the finished resume PDF link to the customer. Called only after
    payment is confirmed and the PDF has been generated and uploaded —
    never call this speculatively or before generation succeeds.
    """
    subject = "Your resume is ready to download"

    html_body = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; color: #1A1A1A;">
      <h2 style="font-size: 18px; margin-bottom: 12px;">Your resume is ready</h2>
      <p style="font-size: 14px; line-height: 1.6;">
        Hi {customer_name or "there"},<br>
        Thanks for your purchase. Your resume PDF is ready to download using the link below.
      </p>
      <p style="margin: 24px 0;">
        <a href="{download_url}"
           style="background: #C76E37; color: #fff; padding: 12px 24px; border-radius: 4px;
                  text-decoration: none; font-weight: 600; font-size: 14px;">
          Download your resume
        </a>
      </p>
      <p style="font-size: 12px; color: #666;">
        This link expires in {expires_in_minutes} minutes and can only be used a limited number of times.
        If it's expired, reply to this email and we'll send a fresh one.
      </p>
    </div>
    """

    text_body = (
        f"Hi {customer_name or 'there'},\n\n"
        f"Your resume PDF is ready: {download_url}\n\n"
        f"This link expires in {expires_in_minutes} minutes.\n"
        f"If it's expired, reply to this email and we'll send a fresh one."
    )

    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM_ADDRESS,
            "to": to_email,
            "subject": subject,
            "html": html_body,
            "text": text_body,
        })
    except Exception as exc:
        # Don't swallow this silently — the caller (pdf_pipeline) needs to
        # know delivery failed so it can retry or flag the order for
        # manual follow-up. A paid customer with no email is a support ticket.
        raise EmailDeliveryError(f"Failed to send resume email to {to_email}") from exc