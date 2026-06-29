"""
Події життєвого циклу застосунку (startup/shutdown через lifespan).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекст життя застосунку: ініціалізація на старті, прибирання на зупинці."""
    logger.info("WeatherTracker API запущено (Swagger UI: /docs)")
    yield
    # Коректно закриваємо зʼєднання з Redis (якщо було відкрите)
    from app.api.utils.redis_client import close_redis_client

    await close_redis_client()
    logger.info("WeatherTracker API зупинено")
