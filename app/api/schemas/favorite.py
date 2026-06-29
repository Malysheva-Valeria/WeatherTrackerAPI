"""Pydantic схеми для улюблених міст."""
from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field

from app.api.schemas.base import BaseSchema
from app.api.schemas.weather import CurrentWeatherResponse


class FavoriteCityCreate(BaseSchema):
    """Запит на додавання міста в обране."""
    city: str = Field(..., min_length=1, max_length=100, description="Назва міста")


class FavoriteCityResponse(BaseSchema):
    """Улюблене місто у відповіді API."""
    id: int
    city: str
    country: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FavoriteWeatherItem(BaseSchema):
    """Улюблене місто разом з поточною погодою (або помилкою)."""
    city: str
    weather: Optional[CurrentWeatherResponse] = None
    error: Optional[str] = None
