import logging

logger = logging.getLogger("auth.email")


class ConsoleEmailSender:
    """Development email sender.

    Instead of contacting a real provider it logs the verification code. This
    keeps local development dependency-free while preserving the same call
    site as the real SMTP transport.
    """

    async def send_verification_code(self, *, email: str, code: str) -> None:
        logger.info("Verification code for %s: %s", email, code)
