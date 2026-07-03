from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Simple human-readable message response."""

    message: str
