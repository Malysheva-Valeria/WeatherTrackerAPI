"""
WeatherTracker API - Основний файл додатку з JWT аутентифікацією
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import uvicorn

# Імпорт конфігурації та залежностей
from app.config import settings
from app.dependencies import get_db
from app.database import SessionLocal

# Імпорт роутерів
from app.api.routers.auth import router as auth_router
from app.api.routers.users import router as users_router
from app.api.routers.weather import router as weather_router
# Створення FastAPI додатку
app = FastAPI(
    title="WeatherTracker API",
    description="API для отримання прогнозу погоди з історією запитів користувачів та JWT аутентифікацією",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware для frontend інтеграції в майбутньому
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшені змінити на конкретні домени
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключення роутерів
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(weather_router)



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


# Подія запуску
@app.on_event("startup")
async def startup_event():
    print("WeatherTracker API запущено")
    print(f" Swagger UI: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    print(f" Доступні ендпойнти аутентифікації:")
    print(f"   POST /auth/register - Реєстрація")
    print(f"   POST /auth/login - Логін")
    print(f"   GET /auth/me - Інформація про користувача")
    print(f"   GET /users/me - Профіль користувача")
    print(f" Погодні ендпойнти:")
    print(f"   GET /weather/current?city=Kyiv - Поточна погода")
    print(f"   GET /weather/history - Історія запитів")
    print(f"   DELETE /weather/history/{{id}} - Видалити запис")
    print(f"   GET /weather/stats - Статистика")


# Подія зупинки
@app.on_event("shutdown")
async def shutdown_event():
    print("WeatherTracker API зупинено")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )