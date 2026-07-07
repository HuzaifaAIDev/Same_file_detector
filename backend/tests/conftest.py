import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key"

TEST_DB_FILE = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

TEST_UPLOAD_DIR = tempfile.mkdtemp()
os.environ["UPLOAD_DIR"] = TEST_UPLOAD_DIR

# No SMTP configured for tests — OTP emails are captured below instead
# of hitting a real mail server.
os.environ["SMTP_HOST"] = ""

from app.database.session import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.database.session import get_db  # noqa: E402
import app.services.email_service as email_service  # noqa: E402

engine = create_engine(f"sqlite:///{TEST_DB_FILE}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Captures the last OTP code sent per (email, purpose), so tests can
# complete OTP flows without a real inbox.
_captured_otps: dict[tuple[str, str], str] = {}


def _fake_send_otp_email(to_email: str, code: str, purpose: str) -> None:
    _captured_otps[(to_email.lower(), purpose)] = code


email_service.send_otp_email = _fake_send_otp_email


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    from app.models import comparison, otp, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    shutil.rmtree(TEST_UPLOAD_DIR, ignore_errors=True)
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def get_otp_code():
    def _get(email: str, purpose: str = "register") -> str:
        return _captured_otps[(email.lower(), purpose)]

    return _get


@pytest.fixture
def registered_user_tokens(client, get_otp_code):
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "username": "testeruser",
            "email": "tester@example.com",
            "password": "Password1!",
            "confirm_password": "Password1!",
        },
    )
    code = get_otp_code("tester@example.com", "register")
    client.post(
        "/api/v1/auth/register/verify",
        json={"email": "tester@example.com", "code": code},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "tester@example.com", "password": "Password1!"},
    )
    return resp.json()


@pytest.fixture
def auth_headers(registered_user_tokens):
    return {"Authorization": f"Bearer {registered_user_tokens['access_token']}"}
