"""
WeatherTracker API - Основний файл додатку з JWT аутентифікацією
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routers import analytics

# Імпорт роутерів
from app.api.routers.auth import router as auth_router
from app.api.routers.users import router as users_router
from app.api.routers.weather import router as weather_router

# Імпорт конфігурації та залежностей
from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Події життєвого циклу застосунку (заміна застарілих on_event)."""
    logger.info("WeatherTracker API запущено (Swagger UI: /docs)")
    yield
    logger.info("WeatherTracker API зупинено")


# Створення FastAPI додатку
app = FastAPI(
    title="WeatherTracker API",
    description="API для отримання прогнозу погоди з історією запитів користувачів та JWT аутентифікацією",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware: список дозволених origin'ів береться з конфігурації
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключення роутерів
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(weather_router)

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
            "Weather Tracking (coming soon)",
            "Request History (coming soon)"
        ],
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Перевірка стану сервісу"""
    return {
        "status": "healthy",
        "service": "WeatherTracker API",
        "version": "1.0.0",
        "database": "connected"
    }


@app.get("/db-test", tags=["Database"])
async def database_test():
    """Тестування підключення до бази даних"""
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 'Database connection successful!' as message"))
        message = result.fetchone()[0]
        db.close()

        from datetime import datetime
        return {
            "status": "success",
            "message": message,
            "timestamp": datetime.now(),
            "database_url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }


@app.get("/models-test", tags=["Database"])
async def models_test():
    """Тестування імпорту моделей"""
    try:
        from app.api.models.user import User

        # Отримання інформації про модель
        model_info = {
            "User": {
                "table_name": User.__tablename__,
                "columns": [column.name for column in User.__table__.columns]
            }
        }

        return {
            "status": "success",
            "message": "Models imported successfully",
            "models": model_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Models import failed: {str(e)}"
        }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
