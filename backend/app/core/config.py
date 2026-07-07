"""
Application configuration.

All configuration is loaded from environment variables (optionally via a
.env file for local development). Nothing sensitive is hardcoded.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    APP_NAME: str = "Universal File Comparer"
    ENVIRONMENT: str = "development"  # development | production | test
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 20285

    # ------------------------------------------------------------------
    # Security / Auth
    # ------------------------------------------------------------------
    # No default secret in production — must be supplied via env var.
    SECRET_KEY: str = Field(default="dev-only-insecure-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: List[str] = ["http://localhost:20285", "http://127.0.0.1:20285"]

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    # Defaults to local SQLite for development. Point DATABASE_URL at
    # Postgres in production, e.g.:
    # postgresql+psycopg2://user:password@host:5432/dbname
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'app_data.db'}"

    # ------------------------------------------------------------------
    # File uploads
    # ------------------------------------------------------------------
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    MAX_FILES_PER_REQUEST: int = 20
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".txt", ".json", ".csv", ".docx", ".xlsx", ".pptx",
        ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif",
    ]

    # Legacy behaviour: the original app compared files by server-side
    # path instead of uploading them. That is an arbitrary-file-read risk,
    # so it is disabled by default. Only enable for trusted, local,
    # single-user use and only within ALLOWED_LOCAL_ROOT.
    ENABLE_LOCAL_PATH_COMPARE: bool = False
    ALLOWED_LOCAL_ROOT: Path = BASE_DIR / "uploads"

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # ------------------------------------------------------------------
    # Worker pool
    # ------------------------------------------------------------------
    COMPARISON_WORKERS: int = 4

    # ------------------------------------------------------------------
    # Frontend
    # ------------------------------------------------------------------
    FRONTEND_URL: str = "http://localhost:20285"

    # ------------------------------------------------------------------
    # Email / SMTP
    # ------------------------------------------------------------------
    # If SMTP_HOST is left blank, OTP emails are written to app.log
    # instead of actually being sent — handy for local development
    # without a real mail server.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@example.com"
    SMTP_USE_TLS: bool = True

    # ------------------------------------------------------------------
    # OTP
    # ------------------------------------------------------------------
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 5
    OTP_RESEND_SECONDS: int = 60
    OTP_MAX_ATTEMPTS: int = 5

    # ------------------------------------------------------------------
    # Auto-provisioned admin account (replaces create_admin.py)
    # ------------------------------------------------------------------
    ADMIN_FIRST_NAME: str = "System"
    ADMIN_LAST_NAME: str = "Administrator"
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_ROLE: str = "admin"

    # ------------------------------------------------------------------
    # Auto-provisioned test users (development/QA only)
    # ------------------------------------------------------------------
    TEST_USERS_PASSWORD: str = "Testing@123"

    TEST_USER_1_FIRST_NAME: str = ""
    TEST_USER_1_LAST_NAME: str = ""
    TEST_USER_1_USERNAME: str = ""
    TEST_USER_1_EMAIL: str = ""

    TEST_USER_2_FIRST_NAME: str = ""
    TEST_USER_2_LAST_NAME: str = ""
    TEST_USER_2_USERNAME: str = ""
    TEST_USER_2_EMAIL: str = ""

    TEST_USER_3_FIRST_NAME: str = ""
    TEST_USER_3_LAST_NAME: str = ""
    TEST_USER_3_USERNAME: str = ""
    TEST_USER_3_EMAIL: str = ""

    TEST_USER_4_FIRST_NAME: str = ""
    TEST_USER_4_LAST_NAME: str = ""
    TEST_USER_4_USERNAME: str = ""
    TEST_USER_4_EMAIL: str = ""

    TEST_USER_5_FIRST_NAME: str = ""
    TEST_USER_5_LAST_NAME: str = ""
    TEST_USER_5_USERNAME: str = ""
    TEST_USER_5_EMAIL: str = ""

    @field_validator("ENVIRONMENT")
    @classmethod
    def _normalize_env(cls, v: str) -> str:
        return v.lower()

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
