from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Registration payload. First and last name are optional."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    """Credentials for issuing a token pair."""

    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    """Email verification payload."""

    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class EmailRequest(BaseModel):
    """Payload carrying only an email address (e.g. resend verification)."""

    email: EmailStr
