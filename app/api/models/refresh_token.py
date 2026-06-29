"""
RefreshToken model — сховище refresh-токенів для ротації та відкликання.

Зберігаємо лише `jti` (ідентифікатор токена), а не сам токен. Це дозволяє
відкликати конкретний refresh-токен (logout) та реалізувати ротацію:
кожне використання інвалідовує старий запис і створює новий.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.api.models.base import Base

if TYPE_CHECKING:
    from app.api.models.user import User


class RefreshToken(Base):
    """Запис про виданий refresh-токен."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<RefreshToken(jti='{self.jti}', user_id={self.user_id}, revoked={self.revoked})>"

    @property
    def is_active(self) -> bool:
        """Токен дійсний: не відкликаний і не протермінований."""
        if self.revoked:
            return False
        expires = self.expires_at
        # SQLite повертає naive datetime — нормалізуємо до UTC для коректного порівняння
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) <= expires
