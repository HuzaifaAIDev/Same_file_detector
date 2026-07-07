"""
Auto-provisions the admin account and predefined test users from
environment variables at application startup. Replaces the old
create_admin.py script — idempotent, so it's safe to run on every boot.
"""
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_logger
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)


def _create_if_missing(
    repo: UserRepository,
    *,
    email: str,
    username: str,
    first_name: str,
    last_name: str,
    password: str,
    role: str,
) -> None:
    if not email or not username:
        return
    if repo.get_by_email(email) or repo.get_by_username(username):
        return  # never duplicate

    repo.create(
        email=email,
        username=username,
        first_name=first_name or username,
        last_name=last_name or "",
        password=password,
        role=role,
        is_verified=True,
        is_active=True,
    )
    logger.info("Seeded %s account: %s", role, email)


def seed_admin_and_test_users(db: Session) -> None:
    repo = UserRepository(db)

    _create_if_missing(
        repo,
        email=settings.ADMIN_EMAIL,
        username=settings.ADMIN_USERNAME,
        first_name=settings.ADMIN_FIRST_NAME,
        last_name=settings.ADMIN_LAST_NAME,
        password=settings.ADMIN_PASSWORD,
        role=settings.ADMIN_ROLE or "admin",
    )

    test_users = [
        (
            settings.TEST_USER_1_EMAIL,
            settings.TEST_USER_1_USERNAME,
            settings.TEST_USER_1_FIRST_NAME,
            settings.TEST_USER_1_LAST_NAME,
        ),
        (
            settings.TEST_USER_2_EMAIL,
            settings.TEST_USER_2_USERNAME,
            settings.TEST_USER_2_FIRST_NAME,
            settings.TEST_USER_2_LAST_NAME,
        ),
        (
            settings.TEST_USER_3_EMAIL,
            settings.TEST_USER_3_USERNAME,
            settings.TEST_USER_3_FIRST_NAME,
            settings.TEST_USER_3_LAST_NAME,
        ),
        (
            settings.TEST_USER_4_EMAIL,
            settings.TEST_USER_4_USERNAME,
            settings.TEST_USER_4_FIRST_NAME,
            settings.TEST_USER_4_LAST_NAME,
        ),
        (
            settings.TEST_USER_5_EMAIL,
            settings.TEST_USER_5_USERNAME,
            settings.TEST_USER_5_FIRST_NAME,
            settings.TEST_USER_5_LAST_NAME,
        ),
    ]

    for email, username, first_name, last_name in test_users:
        _create_if_missing(
            repo,
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=settings.TEST_USERS_PASSWORD,
            role="user",
        )
