from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError
from app.core.logging_config import get_logger
from app.core.security import TokenError, decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

security_logger = get_logger("security")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise AuthError("Not authenticated.")

    try:
        payload = decode_token(token, expected_type="access")
    except TokenError as exc:
        security_logger.info("Rejected invalid/expired access token: %s", exc)
        raise AuthError("Invalid or expired token.") from exc

    user = UserRepository(db).get_by_id(payload.get("sub", ""))
    if not user or not user.is_active:
        raise AuthError("User not found or inactive.")

    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise AuthError("Administrator privileges required.")
    return user
