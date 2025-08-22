"""
Модель ForecastRequest для збереження прогнозів погоди
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.api.models.base import Base


class ForecastRequest(Base):
    """
    Модель для збереження прогнозів погоди на кілька днів

    Зберігає:
    - Інформацію про запит прогнозу
    - Дані прогнозу на кожен день
    - Метадані про джерело даних
    """

    __tablename__ = "forecast_requests"

    # Основні поля
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Локація
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Параметри запиту
    forecast_days = Column(Integer, nullable=False, default=5)  # Кількість днів прогнозу
    request_time = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    # Метадані
    is_cached = Column(Boolean, default=False, nullable=False)
    is_mock = Column(Boolean, default=False, nullable=False)
    cache_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Дані прогнозу (JSON з усіма даними від API)
    forecast_data = Column(JSON, nullable=False)

    # Швидкий доступ до основних показників (для аналітики)
    avg_temperature = Column(Float, nullable=True)  # Середня температура за період
    min_temperature = Column(Float, nullable=True)  # Мінімальна температура
    max_temperature = Column(Float, nullable=True)  # Максимальна температура

    # Часові мітки
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Звʼязки
    user = relationship("User", back_populates="forecast_requests")

    def __repr__(self):
        return f"<ForecastRequest(id={self.id}, city='{self.city}', days={self.forecast_days}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Перевірка чи застарів кешований прогноз"""
        if not self.is_cached or not self.cache_expires_at:
            return True
        return datetime.utcnow() > self.cache_expires_at

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
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DailyForecast(Base):
    """
    Модель для збереження прогнозу на конкретний день
    Детальніша інформація ніж в JSON, для швидких запитів
    """

    __tablename__ = "daily_forecasts"

    # Основні поля
    id = Column(Integer, primary_key=True, index=True)
    forecast_request_id = Column(Integer, ForeignKey("forecast_requests.id", ondelete="CASCADE"), nullable=False,
                                 index=True)

    # Дата прогнозу
    forecast_date = Column(Date, nullable=False, index=True)
    day_offset = Column(Integer, nullable=False)  # 0=сьогодні, 1=завтра, і т.д.

    # Температура
    temperature_min = Column(Float, nullable=False)
    temperature_max = Column(Float, nullable=False)
    temperature_avg = Column(Float, nullable=True)
    feels_like_min = Column(Float, nullable=True)
    feels_like_max = Column(Float, nullable=True)

    # Погодні умови
    weather_condition = Column(String(50), nullable=True)  # Clear, Rain, Snow, etc.
    description = Column(String(200), nullable=True)  # Детальний опис
    icon_code = Column(String(10), nullable=True)  # Код іконки від API

    # Атмосферні умови
    humidity = Column(Integer, nullable=True)  # Вологість %
    pressure = Column(Integer, nullable=True)  # Тиск hPa
    uv_index = Column(Float, nullable=True)  # УФ індекс
    visibility = Column(Float, nullable=True)  # Видимість км

    # Вітер
    wind_speed = Column(Float, nullable=True)  # Швидкість м/с
    wind_direction = Column(Integer, nullable=True)  # Напрямок градуси
    wind_gust = Column(Float, nullable=True)  # Пориви м/с

    # Опади
    precipitation_probability = Column(Integer, nullable=True)  # Ймовірність опадів %
    precipitation_amount = Column(Float, nullable=True)  # Кількість опадів мм

    # Сонце
    sunrise_time = Column(DateTime(timezone=True), nullable=True)
    sunset_time = Column(DateTime(timezone=True), nullable=True)
    daylight_hours = Column(Float, nullable=True)

    # Звʼязки
    forecast_request = relationship("ForecastRequest", backref="daily_forecasts")

    def __repr__(self):
        return f"<DailyForecast(date={self.forecast_date}, temp={self.temperature_min}-{self.temperature_max}°C)>"

    def to_dict(self) -> dict:
        """Конвертація в словник для JSON відповідей"""
        return {
            "date": self.forecast_date.isoformat() if self.forecast_date else None,
            "day_offset": self.day_offset,
            "temperature": {
                "min": self.temperature_min,
                "max": self.temperature_max,
                "avg": self.temperature_avg
            },
            "feels_like": {
                "min": self.feels_like_min,
                "max": self.feels_like_max
            },
            "weather": {
                "condition": self.weather_condition,
                "description": self.description,
                "icon": self.icon_code
            },
            "atmosphere": {
                "humidity": self.humidity,
                "pressure": self.pressure,
                "uv_index": self.uv_index,
                "visibility": self.visibility
            },
            "wind": {
                "speed": self.wind_speed,
                "direction": self.wind_direction,
                "gust": self.wind_gust
            },
            "precipitation": {
                "probability": self.precipitation_probability,
                "amount": self.precipitation_amount
            },
            "sun": {
                "sunrise": self.sunrise_time.isoformat() if self.sunrise_time else None,
                "sunset": self.sunset_time.isoformat() if self.sunset_time else None,
                "daylight_hours": self.daylight_hours
            }
        }