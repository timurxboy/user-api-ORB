from typing import Protocol


class EmailSender(Protocol):
    """Transport-agnostic interface for delivering emails.

    Implementations decide *how* the message is delivered (printed to the log
    in dev, sent over SMTP in prod). The auth service depends only on this
    protocol, so the transport can be swapped via configuration.
    """

    async def send_verification_code(self, *, email: str, code: str) -> None:
        """Deliver a verification code to the given email address."""
        ...
