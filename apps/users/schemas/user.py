from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from apps.users.domain.roles import Role


class UserRead(BaseModel):
    """Public representation of a user."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str | None
    last_name: str | None
    role: Role
    is_verified: bool
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """Partial update payload (PATCH).

    Every field is optional; only the provided fields are applied. Role and
    activation changes are only honoured for admins (enforced in the router).
    """

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    role: Role | None = None
    is_active: bool | None = None
