from pathlib import Path

from fastapi import FastAPI
from sqladmin import Admin

from apps.auth.admin import RefreshTokenAdmin, VerificationCodeAdmin
from apps.auth.utils.admin_auth import AdminAuthBackend
from apps.users.admin.user import UserAdmin
from core.db import engine
from core.settings import core_settings

# Project-level template overrides (e.g. the admin login form labelled "Email").
# Absolute path so the override is found regardless of the working directory.
TEMPLATES_DIR = str(Path(__file__).resolve().parent.parent / "templates")


def setup_admin(app: FastAPI) -> None:
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=AdminAuthBackend(secret_key=core_settings.SECRET_KEY),
        templates_dir=TEMPLATES_DIR,
    )
    admin.add_view(view=UserAdmin)
    admin.add_view(view=RefreshTokenAdmin)
    admin.add_view(view=VerificationCodeAdmin)
