"""
WeatherTracker API - Основний файл додатку з JWT аутентифікацією
"""

import logging

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.core.events import lifespan
from app.api.core.exceptions import register_exception_handlers
from app.api.core.middleware import RequestContextMiddleware
from app.api.core.security import SecurityHeadersMiddleware
from app.api.routers import analytics

# Імпорт роутерів
from app.api.routers.auth import router as auth_router
from app.api.routers.favorites import router as favorites_router
from app.api.routers.users import router as users_router
from app.api.routers.weather import router as weather_router

# Імпорт конфігурації та залежностей
from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)


# Створення FastAPI додатку
app = FastAPI(
    title="WeatherTracker API",
    description="API для отримання прогнозу погоди з історією запитів користувачів та JWT аутентифікацією",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Централізована обробка помилок (єдиний формат + request_id)
register_exception_handlers(app)

# Middleware (порядок: останній доданий — найбільш зовнішній).
# RequestContext має бути зовнішнім, щоб request_id існував для всіх інших.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

# Підключення роутерів
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(weather_router)
app.include_router(favorites_router)

app.include_router(analytics.router, prefix="/api/v1")


# Базові ендпойнти
@app.get("/", tags=["Root"])
async def root():
    """Привітальна сторінка API"""
    return {
        "message": "Welcome to WeatherTracker API!",
        "version": "1.0.0",
        "features": [
            "JWT Authentication",
            "User Management",
            "Weather Tracking",
            "Forecast (5-day)",
            "Request History",
            "Analytics",
        ],
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Перевірка стану сервісу та підключення до БД."""
    database_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: помилка підключення до БД")
        database_ok = False

    return {
        "status": "healthy" if database_ok else "degraded",
        "service": "WeatherTracker API",
        "version": "1.0.0",
        "database": "connected" if database_ok else "unavailable",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
