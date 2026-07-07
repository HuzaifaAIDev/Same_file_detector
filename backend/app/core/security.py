"""
Password hashing and JWT token helpers.

Uses bcrypt directly (no passlib) to avoid the extra dependency's
maintenance issues, and PyJWT for tokens.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

import bcrypt
import jwt
from jwt import PyJWTError

from app.core.config import settings


class TokenError(Exception):
    """Raised when a JWT cannot be decoded/validated."""


# ---------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------
# OTP codes
# ---------------------------------------------------------------------

def generate_otp_code(length: int | None = None) -> str:
    """Cryptographically-random, numeric-only OTP code."""
    length = length or settings.OTP_LENGTH
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp_code(code: str) -> str:
    return hash_password(code)


def verify_otp_code(code: str, code_hash: str) -> bool:
    return verify_password(code, code_hash)


# ---------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------

def _create_token(
    subject: str,
    token_type: Literal["access", "refresh", "reset"],
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": uuid4().hex,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str, role: str = "user") -> str:
    return _create_token(
        subject,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"role": role},
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def create_password_reset_token(email: str, otp_id: str) -> str:
    """Short-lived token proving the holder just completed OTP
    verification for a forgot-password request. Not a login token."""
    return _create_token(
        email,
        "reset",  # type: ignore[arg-type]
        timedelta(minutes=10),
        extra_claims={"otp_id": otp_id},
    )


def decode_token(token: str, expected_type: Literal["access", "refresh", "reset"] | None = None) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except PyJWTError as exc:
        raise TokenError(str(exc)) from exc

    if expected_type and payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token.")

    return payload
