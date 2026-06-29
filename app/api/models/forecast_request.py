"""
Модель ForecastRequest для збереження прогнозів погоди
"""
from datetime import date as date_type
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.api.models.base import Base

if TYPE_CHECKING:
    from app.api.models.user import User


class ForecastRequest(Base):
    """
    Модель для збереження прогнозів погоди на кілька днів
    """

    __tablename__ = "forecast_requests"

    # Основні поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Локація
    city: Mapped[str] = mapped_column(String(100), index=True)
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Параметри запиту
    forecast_days: Mapped[int] = mapped_column(Integer, default=5)
    request_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Метадані
    is_cached: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    cache_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Дані прогнозу (JSON з усіма даними від API)
    forecast_data: Mapped[Any] = mapped_column(JSON)

    # Швидкий доступ до основних показників (для аналітики)
    avg_temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Часові мітки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Звʼязки
    user: Mapped["User"] = relationship(back_populates="forecast_requests")

    def __repr__(self) -> str:
        return f"<ForecastRequest(id={self.id}, city='{self.city}', days={self.forecast_days}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Перевірка чи застарів кешований прогноз"""
        if not self.is_cached or not self.cache_expires_at:
            return True
        return datetime.now(timezone.utc) > self.cache_expires_at

    def to_dict(self) -> dict:
        """Конвертація в словник для JSON відповідей"""
        return {
            "id": self.id,
            "city": self.city,
            "country": self.country,
            "forecast_days": self.forecast_days,
            "request_time": self.request_time.isoformat() if self.request_time else None,
            "is_cached": self.is_cached,
            "is_mock": self.is_mock,
            "avg_temperature": self.avg_temperature,
            "min_temperature": self.min_temperature,
            "max_temperature": self.max_temperature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DailyForecast(Base):
    """
    Модель для збереження прогнозу на конкретний день
    Детальніша інформація ніж в JSON, для швидких запитів
    """

    __tablename__ = "daily_forecasts"

    # Основні поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    forecast_request_id: Mapped[int] = mapped_column(
        ForeignKey("forecast_requests.id", ondelete="CASCADE"), index=True
    )

    # Дата прогнозу
    forecast_date: Mapped[date_type] = mapped_column(Date, index=True)
    day_offset: Mapped[int] = mapped_column(Integer)  # 0=сьогодні, 1=завтра, і т.д.

    # Температура
    temperature_min: Mapped[float] = mapped_column(Float)
    temperature_max: Mapped[float] = mapped_column(Float)
    temperature_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feels_like_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feels_like_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Погодні умови
    weather_condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    icon_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Атмосферні умови
    humidity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pressure: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uv_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    visibility: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Вітер
    wind_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_direction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_gust: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Опади
    precipitation_probability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    precipitation_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Сонце
    sunrise_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sunset_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    daylight_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Звʼязки
    forecast_request: Mapped["ForecastRequest"] = relationship(backref="daily_forecasts")

    def __repr__(self) -> str:
        return f"<DailyForecast(date={self.forecast_date}, temp={self.temperature_min}-{self.temperature_max}°C)>"

    def to_dict(self) -> dict:
        """Конвертація в словник для JSON відповідей"""
        return {
            "date": self.forecast_date.isoformat() if self.forecast_date else None,
            "day_offset": self.day_offset,
            "temperature": {
                "min": self.temperature_min,
                "max": self.temperature_max,
                "avg": self.temperature_avg,
            },
            "feels_like": {
                "min": self.feels_like_min,
                "max": self.feels_like_max,
            },
            "weather": {
                "condition": self.weather_condition,
                "description": self.description,
                "icon": self.icon_code,
            },
            "atmosphere": {
                "humidity": self.humidity,
                "pressure": self.pressure,
                "uv_index": self.uv_index,
                "visibility": self.visibility,
            },
            "wind": {
                "speed": self.wind_speed,
                "direction": self.wind_direction,
                "gust": self.wind_gust,
            },
            "precipitation": {
                "probability": self.precipitation_probability,
                "amount": self.precipitation_amount,
            },
            "sun": {
                "sunrise": self.sunrise_time.isoformat() if self.sunrise_time else None,
                "sunset": self.sunset_time.isoformat() if self.sunset_time else None,
                "daylight_hours": self.daylight_hours,
            },
        }
