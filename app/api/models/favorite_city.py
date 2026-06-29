"""
FavoriteCity model — улюблені міста користувача.

Унікальність гарантується парою (user_id, city): одне місто не можна додати
до обраного двічі.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.api.models.base import Base

if TYPE_CHECKING:
    from app.api.models.user import User


class FavoriteCity(Base):
    """Улюблене місто користувача."""

    __tablename__ = "favorite_cities"
    __table_args__ = (UniqueConstraint("user_id", "city", name="uq_favorite_user_city"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    city: Mapped[str] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<FavoriteCity(user_id={self.user_id}, city='{self.city}')>"
