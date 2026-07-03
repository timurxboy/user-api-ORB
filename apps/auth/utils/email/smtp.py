from email.message import EmailMessage

import aiosmtplib

from core.settings import core_settings


class SMTPEmailSender:
    """Production email sender based on async SMTP.

    Works with any SMTP provider. A convenient free option is Brevo
    (smtp-relay.brevo.com, 300 emails/day) or a Gmail app password. Credentials
    are read from ``SMTP_*`` settings, so switching providers is config-only.
    """

    async def send_verification_code(self, *, email: str, code: str) -> None:
        message = EmailMessage()
        message["From"] = core_settings.SMTP_FROM
        message["To"] = email
        message["Subject"] = "Your verification code"
        message.set_content(
            f"Your verification code is: {code}\n\n"
            "It expires in "
            f"{core_settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes."
        )

        await aiosmtplib.send(
            message,
            hostname=core_settings.SMTP_HOST,
            port=core_settings.SMTP_PORT,
            username=core_settings.SMTP_USER or None,
            password=core_settings.SMTP_PASSWORD or None,
            start_tls=core_settings.SMTP_USE_TLS,
        )
