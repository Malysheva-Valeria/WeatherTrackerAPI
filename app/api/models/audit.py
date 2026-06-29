"""
AuditLog model — журнал чутливих дій (вхід, реєстрація, зміна пароля тощо).

Зберігає хто (user_id), що (action), деталі, звідки (ip_address) та коли.
user_id nullable — напр. невдала спроба входу, де користувач невідомий.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.api.models.base import Base

if TYPE_CHECKING:
    from app.api.models.user import User


# Типи подій
class AuditAction:
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    REGISTER = "register"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    EMAIL_VERIFIED = "email_verified"


class AuditLog(Base):
    """Запис журналу аудиту."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(50), index=True)
    detail: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped[Optional["User"]] = relationship()

    def __repr__(self) -> str:
        return f"<AuditLog(action='{self.action}', user_id={self.user_id}, at={self.created_at})>"
