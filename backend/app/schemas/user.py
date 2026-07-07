from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.validators import validate_password_strength, validate_username


# ---------------------------------------------------------------------
# Registration (Feature 1: Email OTP registration)
# ---------------------------------------------------------------------

class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=150)
    last_name: str = Field(min_length=1, max_length=150)
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        validate_username(v)
        return v.lower()

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        validate_password_strength(v)
        return v

    @model_validator(mode="after")
    def _passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match.")
        return self


class VerifyRegistrationOTPRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendOTPRequest(BaseModel):
    email: EmailStr


# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ---------------------------------------------------------------------
# Forgot password (Feature 3)
# ---------------------------------------------------------------------

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        validate_password_strength(v)
        return v

    @model_validator(mode="after")
    def _passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Password and confirm password do not match.")
        return self


# ---------------------------------------------------------------------
# User output / admin management (Feature 7)
# ---------------------------------------------------------------------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        validate_password_strength(v)
        return v
