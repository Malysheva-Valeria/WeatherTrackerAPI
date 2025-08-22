"""
Ініціалізація моделей WeatherTracker API
"""
from app.api.models.base import Base
from app.api.models.user import User
from app.api.models.weather_request import WeatherRequest
from app.api.models.forecast_request import ForecastRequest, DailyForecast

# Експорт всіх моделей для Alembic
__all__ = [
    "Base",
    "User",
    "WeatherRequest",
    "ForecastRequest",
    "DailyForecast"
]