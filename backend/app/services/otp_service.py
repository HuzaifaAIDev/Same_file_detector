"""
OTP lifecycle: issue, resend (with cooldown), verify (with attempt cap).

Used by both the registration flow (purpose="register", with a JSON
payload of pending user data) and the forgot-password flow
(purpose="reset", no payload).
"""
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import RateLimitError, ValidationAppError
from app.core.security import generate_otp_code, hash_otp_code, verify_otp_code
from app.models.otp import OTPVerification
from app.repositories.otp_repository import OTPRepository
from app.services import email_service


class OTPService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OTPRepository(db)

    def issue(self, email: str, purpose: str, payload: dict | None = None) -> OTPVerification:
        """Create a brand-new OTP, invalidating any previous one for this
        (email, purpose) pair. Used for the *first* send of a flow."""
        email = email.lower()
        existing = self.repo.get_active(email, purpose)
        if existing:
            self.repo.delete(existing)

        return self._create_and_send(email, purpose, payload)

    def resend(self, email: str, purpose: str) -> OTPVerification:
        """Resend for an in-flight flow. Enforces the resend cooldown and
        carries forward the original payload (e.g. pending registration
        data) so the user doesn't have to re-submit the form."""
        email = email.lower()
        existing = self.repo.get_active(email, purpose)
        if not existing:
            raise ValidationAppError(
                "No pending verification found for this email. Please start again."
            )

        now = datetime.now(timezone.utc)
        last_sent = existing.last_sent_at
        if last_sent.tzinfo is None:
            last_sent = last_sent.replace(tzinfo=timezone.utc)
        elapsed = (now - last_sent).total_seconds()
        if elapsed < settings.OTP_RESEND_SECONDS:
            wait = int(settings.OTP_RESEND_SECONDS - elapsed)
            raise RateLimitError(f"Please wait {wait}s before requesting another code.")

        payload = json.loads(existing.payload) if existing.payload else None
        self.repo.delete(existing)
        return self._create_and_send(email, purpose, payload)

    def _create_and_send(
        self, email: str, purpose: str, payload: dict | None
    ) -> OTPVerification:
        code = generate_otp_code()
        now = datetime.now(timezone.utc)
        otp = self.repo.create(
            email=email,
            purpose=purpose,
            code_hash=hash_otp_code(code),
            payload=json.dumps(payload) if payload is not None else None,
            attempts=0,
            max_attempts=settings.OTP_MAX_ATTEMPTS,
            verified=False,
            expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            last_sent_at=now,
        )
        email_service.send_otp_email(email, code, purpose)
        return otp

    def verify(self, email: str, purpose: str, code: str) -> OTPVerification:
        """Validates the code. Raises on failure; on success marks the
        OTP row as verified (caller is responsible for consuming/deleting
        it once done using it)."""
        email = email.lower()
        otp = self.repo.get_active(email, purpose)
        if not otp:
            raise ValidationAppError("No pending verification found for this email.")

        if otp.is_expired():
            self.repo.delete(otp)
            raise ValidationAppError("This code has expired. Please request a new one.")

        if otp.is_locked():
            self.repo.delete(otp)
            raise ValidationAppError(
                "Too many incorrect attempts. Please request a new code."
            )

        if not verify_otp_code(code, otp.code_hash):
            otp.attempts += 1
            self.repo.save(otp)
            remaining = otp.max_attempts - otp.attempts
            if remaining <= 0:
                self.repo.delete(otp)
                raise ValidationAppError(
                    "Too many incorrect attempts. Please request a new code."
                )
            raise ValidationAppError(f"Incorrect code. {remaining} attempt(s) remaining.")

        otp.verified = True
        self.repo.save(otp)
        return otp

    def get_payload(self, otp: OTPVerification) -> dict:
        return json.loads(otp.payload) if otp.payload else {}

    def consume(self, otp: OTPVerification) -> None:
        self.repo.delete(otp)
