from functools import lru_cache

from apps.auth.utils.email.base import EmailSender
from apps.auth.utils.email.console import ConsoleEmailSender
from core.settings import core_settings


@lru_cache
def get_email_sender() -> EmailSender:
    """Return the configured email transport.

    Selected via ``EMAIL_BACKEND`` (``console`` by default). The SMTP transport
    is imported lazily so ``aiosmtplib`` is only required when it is actually
    used.
    """
    if core_settings.EMAIL_BACKEND == "smtp":
        from apps.auth.utils.email.smtp import SMTPEmailSender

        return SMTPEmailSender()

    return ConsoleEmailSender()
