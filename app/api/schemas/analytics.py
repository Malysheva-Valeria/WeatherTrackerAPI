"""
Analytics Pydantic схеми для WeatherTracker API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.api.schemas.base import BaseSchema


class FavoriteCityStats(BaseModel):
    """Статистика улюбленого міста"""
    city: str
    requests: int
    avg_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None


class WeatherConditionStats(BaseModel):
    """Статистика погодних умов"""
    condition: str
    count: int


class ActivityPatterns(BaseModel):
    """Патерни активності користувача"""
    most_active_hour: Optional[int] = None
    most_active_day: Optional[str] = None
    requests_last_30_days: int = 0
    hourly_distribution: Dict[str, int] = Field(default_factory=dict)
    daily_distribution: Dict[str, int] = Field(default_factory=dict)


class LastRequest(BaseModel):
    """Інформація про останній запит"""
    city: Optional[str] = None
    time: Optional[str] = None
    temperature: Optional[float] = None


class UserStatsResponse(BaseSchema):
    """Персональна статистика користувача"""
    user_id: int
    total_requests: int
    weather_requests: int
    forecast_requests: int
    favorite_cities: List[FavoriteCityStats]
    weather_conditions: Dict[str, Any] = Field(default_factory=dict)
    activity_patterns: ActivityPatterns
    last_request: Optional[LastRequest] = None
    generated_at: str


class PopularCityItem(BaseModel):
    """Елемент рейтингу популярних міст"""
    rank: int
    city: str
    country: Optional[str] = None
    total_requests: int
    unique_users: int
    avg_temperature: Optional[float] = None
    first_request: Optional[str] = None
    last_request: Optional[str] = None
    growth_rate: float = 0.0
    requests_last_week: int = 0


class PopularCitiesResponse(BaseSchema):
    """Рейтинг популярних міст"""
    popular_cities: List[PopularCityItem]
    summary: Dict[str, Any] = Field(default_factory=dict)
    generated_at: str


class TemperatureSummary(BaseModel):
    """Підсумок температур"""
    min_temperature: float
    max_temperature: float
    avg_temperature: float
    temperature_range: float


class TrendAnalysis(BaseModel):
    """Аналіз трендів"""
    trend: str  # 'зростає', 'спадає', 'стабільна'
    temperature_change: float
    first_half_avg: float
    second_half_avg: float


class DailyTemperatureData(BaseModel):
    """Температурні дані по днях"""
    date: str
    avg_temperature: float
    min_temperature: float
    max_temperature: float
    requests_count: int


class TemperatureTrendsResponse(BaseSchema):
    """Аналіз температурних трендів"""
    period: str
    city: str
    temperature_summary: TemperatureSummary
    trend_analysis: TrendAnalysis
    daily_data: List[DailyTemperatureData]
    total_data_points: int
    generated_at: str


class ExportFormat(BaseModel):
    """Формат експорту даних"""
    format: str = Field(..., description="Формат: csv, json, pdf")
    period_days: int = Field(30, ge=1, le=365, description="Період в днях")
    include_forecasts: bool = Field(True, description="Включати прогнози")
    include_coordinates: bool = Field(True, description="Включати координати")