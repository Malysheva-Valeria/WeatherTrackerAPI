"""
Weather Pydantic схеми для WeatherTracker API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.api.schemas.base import BaseSchema


class WeatherRequest(BaseSchema):
    """Схема для запиту погоди"""
    city: str = Field(..., min_length=1, max_length=100, description="Назва міста")


class CurrentWeatherResponse(BaseSchema):
    """Схема для відповіді поточної погоди"""
    city: str
    country: str
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    description: str
    condition: str
    humidity: Optional[int] = None
    pressure: Optional[int] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[int] = None
    timestamp: datetime
    cached: bool = False
    mock: bool = False


class WeatherHistoryItem(BaseSchema):
    """Елемент історії погодних запитів"""
    id: int
    city: str
    country: Optional[str] = None
    temperature: Optional[float] = None
    description: Optional[str] = None
    weather_condition: Optional[str] = None
    request_time: datetime
    is_cached: bool = False
    is_mock: bool = False

    model_config = ConfigDict(from_attributes=True)


class WeatherHistoryResponse(BaseSchema):
    """Схема для списку історії погоди"""
    items: List[WeatherHistoryItem]
    total: int
    page: int = 1
    size: int = 10