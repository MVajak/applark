"""OTP delivery. Dev uses a console logger; a real provider implements the same
``EmailSender`` protocol and is swapped in without touching the auth service."""

from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)


class EmailSender(Protocol):
    async def send_otp(self, email: str, code: str) -> None: ...


class ConsoleEmailSender:
    """Logs the OTP to the server console instead of emailing it (development)."""

    async def send_otp(self, email: str, code: str) -> None:
        logger.warning("dev_otp_code", email=email, code=code)
