"""
Налаштування бази даних для WeatherTracker API
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import logging

from app.config import settings

# Налаштування логування SQL запитів
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO if settings.DEBUG else logging.WARNING)

# Створення engine з connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Перевірка з'єднання перед використанням
    echo=settings.DEBUG  # Логування SQL запитів в режимі debug
)

# Створення фабрики сесій
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Імпорт базового класу з моделей
from app.api.models.base import Base


def get_db():
    """
    Dependency для отримання сесії бази даних
    Використовується в FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Створення всіх таблиць в базі даних
    Використовується для ініціалізації БД
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Видалення всіх таблиць з бази даних
    Використовується для очищення БД
    """
    Base.metadata.drop_all(bind=engine)


def test_connection():
    """
    Тестування підключення до бази даних
    True - якщо підключення успішне
    """
    try:
        from sqlalchemy import text

        db = SessionLocal()
        # Простий запит для перевірки
        result = db.execute(text("SELECT 1 as test"))
        db.close()
        return True
    except Exception as e:
        print(f"Помилка підключення до БД: {e}")
        return False


# Метадані для Alembic
def get_database_url():
    """Отримання URL бази даних для Alembic"""
    return settings.DATABASE_URL