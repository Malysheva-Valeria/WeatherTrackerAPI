"""
WeatherTracker API - Основний файл додатку
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Імпорт конфігурації
from app.config import settings

# Створення FastAPI додатку
app = FastAPI(
    title="WeatherTracker API",
    description="API для отримання прогнозу погоди з історією запитів користувачів",
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

# Базові ендпойнти
@app.get("/", tags=["Root"])
async def root():
    """Привітальна сторінка API"""
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

# Подія запуску
@app.on_event("startup")
async def startup_event():
    print("🚀 WeatherTracker API запущено!")
    print(f"📚 Документація доступна за адресою: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")

# Подія зупинки
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 WeatherTracker API зупинено!")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )