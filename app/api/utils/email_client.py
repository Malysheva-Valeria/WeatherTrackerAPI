"""
Низькорівневий клієнт відправки email.

Підтримує бекенд `console` (логування — для dev/тестів) і заготовку під `smtp`.
Усі надіслані повідомлення також складаються в `outbox` — це дозволяє тестам
перевіряти, що лист «надіслано», і діставати з нього токен (як тестова поштова
скринька на кшталт MailHog).
"""
import logging
from dataclasses import dataclass
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SentEmail:
    to: str
    subject: str
    body: str


# Тестова «скринька»: усі надіслані листи (використовується в dev/тестах)
outbox: List[SentEmail] = []


class EmailClient:
    """Відправник email із вибором бекенду через конфіг."""

    def __init__(self) -> None:
        self.backend = settings.EMAIL_BACKEND

    def send(self, to: str, subject: str, body: str) -> None:
        message = SentEmail(to=to, subject=subject, body=body)
        outbox.append(message)

        if self.backend == "smtp":
            self._send_smtp(message)
        else:
            # console-бекенд: лише логуємо (нічого нікуди не відправляємо)
            logger.info("EMAIL -> %s | %s", to, subject)

    def _send_smtp(self, message: SentEmail) -> None:
        """Заготовка під реальний SMTP (потребує SMTP-конфігу в .env)."""
        # Навмисно не реалізовано: у цьому проєкті використовується console-бекенд.
        # Для продакшену сюди підключається smtplib / aiosmtplib.
        logger.warning("SMTP backend не налаштовано; лист до %s не відправлено по-справжньому", message.to)


email_client = EmailClient()


def get_email_client() -> EmailClient:
    return email_client
