"""
EmailService — формування та відправка прикладних листів (верифікація email).
"""
import logging

from app.api.utils.email_client import EmailClient, get_email_client
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Сервіс прикладних email-сценаріїв."""

    def __init__(self, client: EmailClient | None = None) -> None:
        self.client = client or get_email_client()

    def send_verification_email(self, to: str, token: str) -> None:
        """Надіслати лист із посиланням на підтвердження email."""
        link = f"{settings.VERIFY_URL_BASE}?token={token}"
        subject = "Підтвердження email — WeatherTracker"
        body = (
            "Вітаємо у WeatherTracker!\n\n"
            "Підтвердіть вашу адресу, перейшовши за посиланням:\n"
            f"{link}\n\n"
            f"Посилання дійсне {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} год."
        )
        self.client.send(to=to, subject=subject, body=body)
        logger.info("Лист верифікації поставлено в чергу для %s", to)


email_service = EmailService()


def get_email_service() -> EmailService:
    return email_service
