"""
Outbound email for OTP codes.

If SMTP_HOST is not configured (the default for local development), the
email is written to the application log instead of being sent — this
keeps the whole OTP flow runnable out of the box without a mail server.
Configure SMTP_* in .env to send real emails.
"""
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("email")

_SUBJECTS = {
    "register": "Verify your email address",
    "reset": "Reset your password",
}


def _render_body(purpose: str, code: str) -> str:
    action = "complete your registration" if purpose == "register" else "reset your password"
    return (
        f"Your verification code is: {code}\n\n"
        f"Enter this code to {action}. It expires in "
        f"{settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
        f"If you did not request this, you can safely ignore this email."
    )


def send_otp_email(to_email: str, code: str, purpose: str) -> None:
    subject = _SUBJECTS.get(purpose, "Your verification code")
    body = _render_body(purpose, code)

    if not settings.SMTP_HOST:
        # Dev fallback: no SMTP server configured.
        logger.info(
            "SMTP not configured — OTP for %s (%s) is: %s", to_email, purpose, code
        )
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
    except Exception:
        logger.exception("Failed to send OTP email to %s", to_email)
        raise
