"""Email + in-app notifier abstraction.

In-app notifications are persisted as `Notification` rows. Email delivery
is asynchronous: the price-change detector creates a row with
email_status='pending' and the dispatch_email_queue job actually sends.
"""
from __future__ import annotations

import logging
from typing import Protocol

from app.config import Settings, get_settings

log = logging.getLogger(__name__)


class EmailSender(Protocol):
    name: str

    async def send(self, to: str, subject: str, text: str, html: str | None = None) -> None: ...


class ConsoleEmailSender(EmailSender):
    name = "console"

    async def send(self, to: str, subject: str, text: str, html: str | None = None) -> None:
        log.info("[email-console] to=%s subject=%s\n%s", to, subject, text)


class SMTPEmailSender(EmailSender):
    name = "smtp"

    def __init__(self, host: str, port: int, user: str | None, password: str | None, sender: str):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from = sender

    async def send(self, to: str, subject: str, text: str, html: str | None = None) -> None:
        import aiosmtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = self._from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(text)
        if html:
            msg.add_alternative(html, subtype="html")
        await aiosmtplib.send(
            msg,
            hostname=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
            start_tls=self._port == 587,
            use_tls=self._port == 465,
        )


def get_email_sender(settings: Settings | None = None) -> EmailSender:
    settings = settings or get_settings()
    backend = (settings.notifier_backend or "console").lower()
    if backend == "smtp" and settings.smtp_host and settings.smtp_from:
        return SMTPEmailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            user=settings.smtp_user,
            password=settings.smtp_password,
            sender=settings.smtp_from,
        )
    return ConsoleEmailSender()
