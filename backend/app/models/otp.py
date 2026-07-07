"""
OTP verification model.

Backs two flows:
  - "register": a pending sign-up. `payload` holds the JSON-encoded
    first/last name, username, email and *already-hashed* password. The
    User row is only created once the OTP is verified.
  - "reset": a forgot-password request for an existing user. `payload`
    is unused (None).

One row per in-flight verification per (email, purpose). Resending
invalidates the previous code (new code + reset attempts + reset
expiry), satisfying "old OTP becomes invalid after resend".
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)  # register | reset

    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def is_expired(self) -> bool:
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expires_at

    def is_locked(self) -> bool:
        return self.attempts >= self.max_attempts
