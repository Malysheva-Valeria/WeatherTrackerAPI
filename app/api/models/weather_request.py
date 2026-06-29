"""
WeatherRequest model для збереження історії погодних запитів
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.api.models.base import Base


class WeatherRequest(Base):
    """Модель для збереження історії погодних запитів користувачів"""

    __tablename__ = "weather_requests"

    # Основні поля
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Дані про місто
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(10), nullable=True)

    # Погодні дані
    temperature = Column(Numeric(5, 2), nullable=True)  # -99.99 до 99.99
    feels_like = Column(Numeric(5, 2), nullable=True)
    description = Column(String(200), nullable=True)
    weather_condition = Column(String(50), nullable=True)  # Clear, Clouds, Rain тощо

    # Додаткові дані
    humidity = Column(Integer, nullable=True)  # %
    pressure = Column(Integer, nullable=True)  # hPa
    wind_speed = Column(Numeric(5, 2), nullable=True)  # м/с
    wind_direction = Column(Integer, nullable=True)  # градуси

    # Метадані
    request_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_data = Column(JSON, nullable=True)  # Повні дані з API
    is_cached = Column(Boolean, default=False, nullable=False)  # Чи був запит з кешу
    is_mock = Column(Boolean, default=False, nullable=False)  # Чи використовувались mock дані

    # Зв'язки
    user = relationship("User", back_populates="weather_requests")

    def __repr__(self):
        return f"<WeatherRequest(id={self.id}, user_id={self.user_id}, city='{self.city}', temp={self.temperature})>"

    def to_dict(self) -> dict:
        """Конвертація в словник для JSON відповідей"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "city": self.city,
            "country": self.country,
            "temperature": float(self.temperature) if self.temperature else None,
            "feels_like": float(self.feels_like) if self.feels_like else None,
            "description": self.description,
            "weather_condition": self.weather_condition,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": float(self.wind_speed) if self.wind_speed else None,
            "wind_direction": self.wind_direction,
            "request_time": self.request_time.isoformat() if self.request_time else None,
            "is_cached": self.is_cached,
            "is_mock": self.is_mock
        }
