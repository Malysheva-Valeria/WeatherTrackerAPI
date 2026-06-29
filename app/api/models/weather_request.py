"""
WeatherRequest model для збереження історії погодних запитів
"""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.api.models.base import Base

if TYPE_CHECKING:
    from app.api.models.user import User


class WeatherRequest(Base):
    """Модель для збереження історії погодних запитів користувачів"""

    __tablename__ = "weather_requests"

    # Основні поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Дані про місто
    city: Mapped[str] = mapped_column(String(100), index=True)
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Погодні дані
    temperature: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # -99.99 до 99.99
    feels_like: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    weather_condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Clear, Clouds, Rain тощо

    # Додаткові дані
    humidity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # %
    pressure: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # hPa
    wind_speed: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # м/с
    wind_direction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # градуси

    # Метадані
    request_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    response_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Повні дані з API
    is_cached: Mapped[bool] = mapped_column(Boolean, default=False)  # Чи був запит з кешу
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)  # Чи використовувались mock дані

    # Зв'язки
    user: Mapped["User"] = relationship(back_populates="weather_requests")

    def __repr__(self) -> str:
        return f"<WeatherRequest(id={self.id}, user_id={self.user_id}, city='{self.city}', temp={self.temperature})>"

    def to_dict(self) -> dict:
        """Конвертація в словник для JSON відповідей"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "city": self.city,
            "country": self.country,
            "temperature": float(self.temperature) if self.temperature is not None else None,
            "feels_like": float(self.feels_like) if self.feels_like is not None else None,
            "description": self.description,
            "weather_condition": self.weather_condition,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": float(self.wind_speed) if self.wind_speed is not None else None,
            "wind_direction": self.wind_direction,
            "request_time": self.request_time.isoformat() if self.request_time else None,
            "is_cached": self.is_cached,
            "is_mock": self.is_mock,
        }
