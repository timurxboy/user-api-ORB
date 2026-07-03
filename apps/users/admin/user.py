from typing import ClassVar

import wtforms
from sqladmin import ModelView

from apps.users.domain.roles import Role
from apps.users.models.user import User
from core.security import hash_password


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"

    column_list: ClassVar = [
        User.id,
        User.email,
        User.role,
        User.is_verified,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list: ClassVar = [User.email]
    column_sortable_list: ClassVar = [
        User.id,
        User.email,
        User.is_verified,
        User.is_active,
        User.created_at,
    ]
    column_labels: ClassVar = {"password_hashed": "Password"}

    # Render `role` as a dropdown of valid roles instead of a free-text field,
    # so an admin can only ever store an exact enum value ("user" / "admin").
    form_overrides: ClassVar = {"role": wtforms.SelectField}
    form_args: ClassVar = {
        "role": {
            "choices": [(role.value, role.name.capitalize()) for role in Role],
        },
        # Password is write-only: leave blank on edit to keep the current one.
        "password_hashed": {"validators": [wtforms.validators.Optional()]},
    }

    form_create_rules: ClassVar = [
        "email",
        "password_hashed",
        "first_name",
        "last_name",
        "role",
        "is_verified",
        "is_active",
    ]
    form_edit_rules: ClassVar = form_create_rules

    async def on_model_change(
        self,
        data: dict,
        model: User,
        is_created: bool,
        request,
    ) -> None:
        password = data.get("password_hashed")
        if password:
            # A new password was entered — hash it.
            data["password_hashed"] = hash_password(password)
        elif is_created:
            # No password on create would store an unusable empty hash.
            raise ValueError("Password is required when creating a user")
        else:
            # Editing without a new password: keep the stored hash untouched.
            data.pop("password_hashed", None)
