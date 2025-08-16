"""
Конфігурація додатку WeatherTracker
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Налаштування додатку"""

    # Database settings
    DATABASE_URL: str = "postgresql://weather_user:password@localhost:5432/weathertracker"

    # JWT settings
    SECRET_KEY: str = "your-super-secret-jwt-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenWeather API settings
    OPENWEATHER_API_KEY: Optional[str] = None
    OPENWEATHER_BASE_URL: str = "http://api.openweathermap.org/data/2.5"

    # Application settings
    DEBUG: bool = True
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # Cache settings
    CACHE_TTL: int = 600  # 10 хвилин
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        """Конфігурація для читання з .env файлу"""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Створення екземпляру налаштувань
settings = Settings()


def get_settings() -> Settings:
    """Отримати налаштування додатку"""
    return settings