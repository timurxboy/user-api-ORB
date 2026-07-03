import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from core.settings import core_settings

ALGORITHM = "HS256"


def create_access_token(*, subject: int, role: str, minutes: int | None = None) -> str:
    if minutes is None:
        minutes = core_settings.ACCESS_TOKEN_EXPIRE_MINUTES

    payload = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, core_settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token() -> str:
    return str(uuid.uuid4())


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        jwt=token,
        key=core_settings.SECRET_KEY,
        algorithms=[ALGORITHM],
    )
