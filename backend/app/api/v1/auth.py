from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import AuthError, ConflictError, ValidationAppError
from app.core.logging_config import get_logger
from app.core.security import (
    TokenError,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    RefreshRequest,
    RegisterRequest,
    ResendOTPRequest,
    ResetPasswordRequest,
    TokenPair,
    UserLogin,
    UserOut,
    VerifyRegistrationOTPRequest,
    VerifyResetOTPRequest,
)
from app.services.otp_service import OTPService

router = APIRouter(prefix="/auth", tags=["auth"])
security_logger = get_logger("security")


def _issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id, role=user.role),
        refresh_token=create_refresh_token(user.id),
    )


# ---------------------------------------------------------------------
# Registration (Feature 1) — the user is only created after OTP verify.
# ---------------------------------------------------------------------

@router.post("/register", status_code=202)
def register_request(payload: RegisterRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_by_email(payload.email):
        raise ConflictError("An account with this email already exists.")
    if repo.get_by_username(payload.username):
        raise ConflictError("This username is already taken.")

    from app.core.security import hash_password

    pending = {
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "username": payload.username,
        "email": payload.email.lower(),
        "hashed_password": hash_password(payload.password),
    }
    OTPService(db).issue(payload.email, "register", payload=pending)
    security_logger.info("Registration OTP issued for %s", payload.email)
    return {
        "success": True,
        "message": "We've sent a 6-digit verification code to your email.",
    }


@router.post("/register/verify", response_model=UserOut, status_code=201)
def register_verify(payload: VerifyRegistrationOTPRequest, db: Session = Depends(get_db)):
    otp_service = OTPService(db)
    otp = otp_service.verify(payload.email, "register", payload.code)
    data = otp_service.get_payload(otp)

    repo = UserRepository(db)
    if repo.get_by_email(data["email"]) or repo.get_by_username(data["username"]):
        otp_service.consume(otp)
        raise ConflictError("An account with this email or username already exists.")

    user = User(
        email=data["email"],
        username=data["username"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        hashed_password=data["hashed_password"],
        role="user",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    otp_service.consume(otp)

    security_logger.info("Registration completed for %s", user.email)
    return user


@router.post("/register/resend", status_code=202)
def register_resend(payload: ResendOTPRequest, db: Session = Depends(get_db)):
    OTPService(db).resend(payload.email, "register")
    return {"success": True, "message": "A new verification code has been sent."}


# ---------------------------------------------------------------------
# Login (Feature 2)
# ---------------------------------------------------------------------

@router.post("/login", response_model=TokenPair)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_email(payload.email)

    if not user or not verify_password(payload.password, user.hashed_password):
        security_logger.info("Failed login attempt for %s", payload.email)
        raise AuthError("Incorrect email or password.")

    if not user.is_verified:
        raise AuthError("Please verify your email address before signing in.")

    if not user.is_active:
        raise AuthError("This account has been suspended.")

    security_logger.info("Successful login: %s", user.email)
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise AuthError("Invalid or expired refresh token.") from exc

    user = UserRepository(db).get_by_id(claims.get("sub", ""))
    if not user or not user.is_active:
        raise AuthError("User not found or inactive.")

    return _issue_tokens(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise AuthError("Current password is incorrect.")

    UserRepository(db).set_password(current_user, payload.new_password)
    security_logger.info("Password changed for %s", current_user.email)


# ---------------------------------------------------------------------
# Forgot password (Feature 3)
# ---------------------------------------------------------------------

@router.post("/forgot-password", status_code=202)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_email(payload.email)
    # Always respond the same way whether or not the account exists, to
    # avoid leaking which emails are registered.
    if user:
        OTPService(db).issue(payload.email, "reset")
        security_logger.info("Password-reset OTP issued for %s", payload.email)
    return {
        "success": True,
        "message": "If an account exists for this email, a verification code has been sent.",
    }


@router.post("/forgot-password/resend", status_code=202)
def forgot_password_resend(payload: ResendOTPRequest, db: Session = Depends(get_db)):
    OTPService(db).resend(payload.email, "reset")
    return {"success": True, "message": "A new verification code has been sent."}


@router.post("/forgot-password/verify")
def forgot_password_verify(payload: VerifyResetOTPRequest, db: Session = Depends(get_db)):
    otp_service = OTPService(db)
    otp = otp_service.verify(payload.email, "reset", payload.code)
    reset_token = create_password_reset_token(payload.email.lower(), otp.id)
    return {"reset_token": reset_token}


@router.post("/reset-password", status_code=204)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        claims = decode_token(payload.reset_token, expected_type="reset")
    except TokenError as exc:
        raise ValidationAppError(
            "This reset link is invalid or has expired. Please start again."
        ) from exc

    email = claims.get("sub", "")
    otp_id = claims.get("otp_id")

    otp_service = OTPService(db)
    otp = otp_service.repo.get_active(email, "reset")
    if not otp or otp.id != otp_id or not otp.verified:
        raise ValidationAppError(
            "This reset link is invalid or has expired. Please start again."
        )

    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if not user:
        raise ValidationAppError("Account not found.")

    repo.set_password(user, payload.new_password)
    otp_service.consume(otp)
    security_logger.info("Password reset completed for %s", email)
