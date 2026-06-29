"""
Конфігурація додатку WeatherTracker
"""
from typing import List, Optional, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

# Значення-плейсхолдери, які заборонено використовувати в продакшені
INSECURE_SECRETS = {
    "your-super-secret-jwt-key-here-change-in-production",
    "change-in-production",
    "secret",
    "",
}


class Settings(BaseSettings):
    """Налаштування додатку"""

    # Середовище виконання: development | production
    ENVIRONMENT: str = "development"

    # Database settings
    DATABASE_URL: str = "postgresql://weather_user:password@localhost:5432/weathertracker"

    # JWT settings
    # У dev використовується небезпечний дефолт; у production значення обовʼязкове
    # і перевіряється валідатором нижче.
    SECRET_KEY: str = "your-super-secret-jwt-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenWeather API settings
    OPENWEATHER_API_KEY: Optional[str] = None
    OPENWEATHER_BASE_URL: str = "http://api.openweathermap.org/data/2.5"

    # Weather service settings
    WEATHER_CACHE_TTL: int = 600  # 10 хвилин
    WEATHER_TIMEOUT: int = 10  # 10 секунд
    WEATHER_USE_MOCK: bool = False

    # Application settings
    DEBUG: bool = False
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # CORS: список дозволених origin'ів (кома-розділений рядок у .env)
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Cache settings
    CACHE_TTL: int = 600  # 10 хвилин
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Дозволяє задавати CORS origins як кома-розділений рядок у .env"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def _enforce_production_safety(self) -> "Settings":
        """У продакшені забороняємо небезпечні дефолти секретів та DEBUG."""
        if self.is_production:
            if self.SECRET_KEY in INSECURE_SECRETS:
                raise ValueError(
                    "SECRET_KEY має бути встановлений у безпечне значення для production "
                    "(згенеруйте, напр., `openssl rand -hex 32`)."
                )
            if self.DEBUG:
                raise ValueError("DEBUG має бути False у production.")
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("CORS '*' заборонено у production — вкажіть конкретні домени.")
        return self

    class Config:
        """Конфігурація для читання з .env файлу"""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Створення екземпляра налаштувань
settings = Settings()


def get_settings() -> Settings:
    """Отримання налаштування додатку"""
    return settings
