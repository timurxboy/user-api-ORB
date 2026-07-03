import logging
import os
from logging.handlers import TimedRotatingFileHandler

from core.settings import core_settings

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Marks handlers this module installed, so setup stays idempotent across calls
# (e.g. lifespan startup) without duplicating output.
_APP_HANDLER_FLAG = "_app_handler"


def setup_logger(name: str = "app") -> logging.Logger:
    """Configure application logging.

    Handlers are attached to the **root** logger so that every module's logger
    (``main``, ``auth.email``, ...) propagates to the same console + file
    output. Returns the named logger for convenience.
    """
    os.makedirs(core_settings.LOG_DIR, exist_ok=True)
    log_path = os.path.join(core_settings.LOG_DIR, core_settings.LOG_FILE)

    root = logging.getLogger()
    root.setLevel(core_settings.LOG_LEVEL)

    already_configured = any(
        getattr(handler, _APP_HANDLER_FLAG, False) for handler in root.handlers
    )
    if not already_configured:
        formatter = logging.Formatter(LOG_FORMAT)

        file_handler = TimedRotatingFileHandler(
            filename=log_path,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        for handler in (file_handler, console_handler):
            setattr(handler, _APP_HANDLER_FLAG, True)
            root.addHandler(handler)

    logger = logging.getLogger(name)
    logger.setLevel(core_settings.LOG_LEVEL)
    return logger
