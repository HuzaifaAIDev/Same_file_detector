from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password: str,
        role: str = "user",
        is_verified: bool = False,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email.lower(),
            username=username.lower(),
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password),
            role=role,
            is_verified=is_verified,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_password(self, user: User, new_password: str) -> None:
        user.hashed_password = hash_password(new_password)
        self.db.commit()

    def mark_verified(self, user: User) -> None:
        user.is_verified = True
        self.db.commit()

    def set_active(self, user: User, active: bool) -> None:
        user.is_active = active
        self.db.commit()

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
