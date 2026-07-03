from fastapi import FastAPI

from apps.auth.api.router import router as auth_router
from apps.users.api.router import router as users_router


def setup_routers(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(users_router)
