"""
Ініціалізація моделей WeatherTracker API
"""
from app.api.models.base import Base
from app.api.models.forecast_request import DailyForecast, ForecastRequest
from app.api.models.refresh_token import RefreshToken
from app.api.models.user import User
from app.api.models.weather_request import WeatherRequest

# Експорт всіх моделей для Alembic
__all__ = [
    "Base",
    "User",
    "WeatherRequest",
    "ForecastRequest",
    "DailyForecast",
    "RefreshToken",
]
