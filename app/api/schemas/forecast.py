"""
Виправлені Pydantic схеми для прогнозів погоди
app/api/schemas/forecast.py
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from app.api.schemas.base import TimestampSchema


class TemperatureData(BaseModel):
    """Схема для температурних даних"""
    min: Optional[float] = Field(None, description="Мінімальна температура")
    max: Optional[float] = Field(None, description="Максимальна температура")
    avg: Optional[float] = Field(None, description="Середня температура")


class FeelsLikeData(BaseModel):
    """Схема для відчувається як"""
    min: Optional[float] = Field(None, description="Мінімально відчувається")
    max: Optional[float] = Field(None, description="Максимально відчувається")


class WeatherConditionData(BaseModel):
    """Схема для погодних умов"""
    condition: Optional[str] = Field(None, description="Стан погоди")
    description: Optional[str] = Field(None, description="Детальний опис")
    icon: Optional[str] = Field(None, description="Код іконки")


class AtmosphereData(BaseModel):
    """Схема для атмосферних показників"""
    humidity: Optional[int] = Field(None, description="Вологість %")
    pressure: Optional[int] = Field(None, description="Атмосферний тиск hPa")
    uv_index: Optional[float] = Field(None, description="УФ індекс")
    visibility: Optional[float] = Field(None, description="Видимість км")


class WindData(BaseModel):
    """Схема для вітрових умов"""
    speed: Optional[float] = Field(None, description="Швидкість вітру м/с")
    direction: Optional[int] = Field(None, description="Напрямок вітру градуси")
    gust: Optional[float] = Field(None, description="Пориви вітру м/с")


class PrecipitationData(BaseModel):
    """Схема для опадів"""
    probability: Optional[int] = Field(None, description="Ймовірність опадів %")
    amount: Optional[float] = Field(None, description="Кількість опадів мм")


class SunData(BaseModel):
    """Схема для інформації про сонце"""
    sunrise: Optional[str] = Field(None, description="Час сходу сонця")
    sunset: Optional[str] = Field(None, description="Час заходу сонця")
    daylight_hours: Optional[float] = Field(None, description="Годин світлого часу")


class DailyForecastData(BaseModel):
    """Схема для даних прогнозу на один день"""

    forecast_date: date = Field(..., description="Дата прогнозу")
    day_offset: int = Field(..., description="Зміщення від сьогодні (0=сьогодні, 1=завтра)")

    # Структуровані дані
    temperature: TemperatureData = Field(..., description="Температурні показники")
    feels_like: Optional[FeelsLikeData] = Field(None, description="Відчувається як")
    weather: WeatherConditionData = Field(..., description="Погодні умови")
    atmosphere: Optional[AtmosphereData] = Field(None, description="Атмосферні показники")
    wind: Optional[WindData] = Field(None, description="Вітрові умови")
    precipitation: Optional[PrecipitationData] = Field(None, description="Інформація про опади")
    sun: Optional[SunData] = Field(None, description="Інформація про сонце")


class ForecastRequestSchema(BaseModel):
    """Схема запиту прогнозу погоди"""

    city: Optional[str] = Field(None, min_length=1, max_length=100, description="Назва міста")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Широта")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Довгота")
    days: int = Field(5, ge=1, le=7, description="Кількість днів прогнозу (1-7)")

    @validator('city')
    def validate_location_provided(cls, v, values):
        """Перевірити що вказано або місто, або координати"""
        lat = values.get('latitude')
        lon = values.get('longitude')

        # Якщо є місто - ОК
        if v and v.strip():
            return v.strip()

        # Якщо немає міста, мають бути координати
        if lat is None or lon is None:
            raise ValueError('Вкажіть або назву міста, або координати (latitude + longitude)')

        return v

    class Config:
        schema_extra = {
            "examples": [
                {
                    "city": "Kyiv",
                    "days": 5
                },
                {
                    "latitude": 50.4501,
                    "longitude": 30.5234,
                    "days": 3
                }
            ]
        }


class ForecastSummary(BaseModel):
    """Загальна статистика прогнозу"""
    avg_temperature: Optional[float] = Field(None, description="Середня температура")
    min_temperature: Optional[float] = Field(None, description="Мінімальна температура")
    max_temperature: Optional[float] = Field(None, description="Максимальна температура")
    dominant_condition: Optional[str] = Field(None, description="Переважний стан погоди")
    rainy_days: Optional[int] = Field(None, description="Дощових днів")
    precipitation_total: Optional[float] = Field(None, description="Загальна кількість опадів мм")


class ForecastResponse(BaseModel):
    """Схема відповіді з прогнозом погоди (БЕЗ TimestampSchema)"""

    # Локація
    city: str = Field(..., description="Назва міста")
    country: Optional[str] = Field(None, description="Код країни")
    latitude: Optional[float] = Field(None, description="Широта")
    longitude: Optional[float] = Field(None, description="Довгота")

    # Параметри запиту
    forecast_days: int = Field(..., description="Кількість днів прогнозу")
    request_time: datetime = Field(..., description="Час запиту")

    # Прогноз по днях
    daily_forecasts: List[DailyForecastData] = Field(..., description="Прогноз по днях")

    # Сумарна статистика
    summary: ForecastSummary = Field(..., description="Загальна статистика по прогнозу")

    # Метадані
    cached: bool = Field(False, description="Чи отримано з кешу")
    mock: bool = Field(default=False, description="Чи це тестові дані")
    expires_at: Optional[datetime] = Field(None, description="Час закінчення кешу")

    model_config = {
        "json_schema_extra": {
            "example": {
                "city": "Kyiv",
                "country": "UA",
                "latitude": 50.4333,
                "longitude": 30.5167,
                "forecast_days": 5,
                "request_time": "2025-08-20T10:30:00",
                "daily_forecasts": [],
                "summary": {
                    "avg_temperature": 20.0,
                    "min_temperature": 15.0,
                    "max_temperature": 25.0,
                    "dominant_condition": "Clear",
                    "rainy_days": 0,
                    "precipitation_total": 0.0
                },
                "cached": False,
                "mock": False
            }
        }
    }


class ForecastHistoryItem(TimestampSchema):
    """Елемент історії прогнозів"""

    id: int = Field(..., description="ID запису")
    city: str = Field(..., description="Місто")
    country: Optional[str] = Field(None, description="Країна")
    forecast_days: int = Field(..., description="Кількість днів прогнозу")
    request_time: datetime = Field(..., description="Час запиту")

    # Основні показники
    avg_temperature: Optional[float] = Field(None, description="Середня температура")
    min_temperature: Optional[float] = Field(None, description="Мінімальна температура")
    max_temperature: Optional[float] = Field(None, description="Максимальна температура")

    # Метадані
    is_cached: bool = Field(..., description="Чи був закешований")
    is_mock: bool = Field(..., description="Чи це mock дані")

    class Config:
        from_attributes = True


class ForecastHistoryResponse(BaseModel):
    """Відповідь зі списком історії прогнозів"""

    items: List[ForecastHistoryItem] = Field(..., description="Список прогнозів")
    total: int = Field(..., description="Загальна кількість записів")
    page: int = Field(..., description="Поточна сторінка")
    size: int = Field(..., description="Розмір сторінки")
    pages: int = Field(..., description="Загальна кількість сторінок")

    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        """Розрахувати кількість сторінок"""
        total = values.get('total', 0)
        size = values.get('size', 10)
        return max(1, (total + size - 1) // size)


class PopularCityData(BaseModel):
    """Дані про популярне місто"""
    city: Optional[str] = Field(None, description="Назва міста")
    forecasts_count: int = Field(0, description="Кількість прогнозів")
    avg_days: Optional[float] = Field(None, description="Середня кількість днів в прогнозі")


class TemperatureStatsData(BaseModel):
    """Статистика температур"""
    overall_avg: Optional[float] = Field(None, description="Загальна середня температура")
    overall_min: Optional[float] = Field(None, description="Мінімальна температура")
    overall_max: Optional[float] = Field(None, description="Максимальна температура")
    avg_daily_range: Optional[float] = Field(None, description="Середній добовий діапазон")


class UsageStatsData(BaseModel):
    """Статистика використання"""
    first_forecast: Optional[datetime] = Field(None, description="Перший прогноз")
    last_forecast: Optional[datetime] = Field(None, description="Останній прогноз")
    avg_forecasts_per_day: Optional[float] = Field(None, description="Середня кількість прогнозів на день")
    most_active_day: Optional[str] = Field(None, description="Найактивніший день тижня")


class ForecastStatsResponse(BaseModel):
    """Статистика прогнозів користувача"""

    total_forecasts: int = Field(..., description="Загальна кількість прогнозів")
    unique_cities: int = Field(..., description="Унікальних міст")
    total_days_forecasted: int = Field(..., description="Загалом днів спрогнозовано")

    # Топ статистики
    most_popular_city: PopularCityData = Field(..., description="Найпопулярніше місто")

    # Температурна статистика
    temperature_stats: TemperatureStatsData = Field(..., description="Статистика температур")

    # Часова статистика
    usage_stats: UsageStatsData = Field(..., description="Статистика використання")