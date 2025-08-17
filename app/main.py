"""
WeatherTracker API - Основний файл
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

# Імпорти проєкту
from app.config import settings
from app.database import get_db, test_connection

# Створення FastAPI додатку
app = FastAPI(
    title="WeatherTracker API",
    description="API для отримання прогнозу погоди з історією запитів користувачів",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware для frontend інтеграції
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшені змінити на конкретні домени
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Базові ендпойнти
@app.get("/", tags=["Root"])
async def root():
    """Main сторінка API"""
    return {
        "message": "Welcome to WeatherTracker API!",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Перевірка стану сервісу"""
    return {
        "status": "healthy",
        "service": "WeatherTracker API",
        "version": "1.0.0"
    }


@app.get("/db-test", tags=["Database"])
async def database_test(db: Session = Depends(get_db)):
    """Тестування підключення до бази даних"""
    try:
        from sqlalchemy import text

        result = db.execute(text("SELECT 'Database connection successful!' as message, NOW() as timestamp"))
        row = result.fetchone()

        return {
            "status": "success",
            "message": row[0],
            "timestamp": row[1],
            "database_url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "hidden"
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
        from app.api.models import User, BaseModel

        return {
            "status": "success",
            "message": "Models imported successfully",
            "models": {
                "User": {
                    "table_name": User.__tablename__,
                    "columns": [column.name for column in User.__table__.columns]
                }
            }
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
    print(f"Документація: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")

    # Тестування підключення до БД
    if test_connection():
        print("База даних підключена")
    else:
        print("Помилка підключення до бази даних")


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