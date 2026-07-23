# app/services/email.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import get_settings

settings = get_settings()


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
    Sends the finished resume PDF link to the customer via SendGrid's HTTPS
    API. Called only after payment is confirmed and the PDF has been
    generated and uploaded — never call this speculatively or before
    generation succeeds.

    Uses HTTPS (port 443) rather than SMTP deliberately — many hosts
    (Railway included, on Free/Trial/Hobby plans) block outbound SMTP
    ports (25/465/587) entirely, which an HTTPS API call never hits.
    """
    expires_in_hours = round(expires_in_minutes / 60, 1)
    expires_in_days = round(expires_in_minutes / (60 * 24), 1)

    if expires_in_minutes < 60:
        expiry_text = f"{expires_in_minutes} minutes"
    elif expires_in_minutes < 1440:
        expiry_text = f"{expires_in_hours} hours"
    elif expires_in_days==1:
        expiry_text = f"{expires_in_days} day"
    else:
        expiry_text = f"{expires_in_days} days"
  
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
        This link expires in {expiry_text} and can only be used a limited number of times.
        If it's expired, reply to this email and we'll send a fresh one.
      </p>
    </div>
    """

    text_body = (
        f"Hi {customer_name or 'there'},\n\n"
        f"Your resume PDF is ready: {download_url}\n\n"
        f"This link expires in {expiry_text}.\n"
        f"If it's expired, reply to this email and we'll send a fresh one."
    )

    message = Mail(
        from_email=settings.EMAIL_FROM_ADDRESS,  # must match your SendGrid Single Sender Verified address
        to_emails=to_email,
        subject=subject,
        plain_text_content=text_body,
        html_content=html_body,
    )

    try:
        client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = client.send(message)
        if response.status_code >= 300:
            raise EmailDeliveryError(
                f"SendGrid rejected the email to {to_email} (status {response.status_code}): {response.body}"
            )
    except EmailDeliveryError:
        raise
    except Exception as exc:
        raise EmailDeliveryError(f"Failed to send resume email to {to_email}") from exc