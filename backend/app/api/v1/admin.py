from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging_config import get_logger
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])
security_logger = get_logger("security")


@router.get("/users", response_model=list[UserOut])
def list_users(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return UserRepository(db).list_all()


@router.post("/users/{user_id}/suspend", response_model=UserOut)
def suspend_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_admin.id:
        raise ForbiddenError("You cannot suspend your own account.")

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found.")

    repo.set_active(user, False)
    security_logger.info("User suspended: %s by %s", user.email, current_admin.email)
    return user


@router.post("/users/{user_id}/activate", response_model=UserOut)
def activate_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found.")

    repo.set_active(user, True)
    security_logger.info("User reactivated: %s by %s", user.email, current_admin.email)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_admin.id:
        raise ForbiddenError("You cannot delete your own account.")

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise NotFoundError("User not found.")

    security_logger.info("User deleted: %s by %s", user.email, current_admin.email)
    repo.delete(user)
