"""Глобальні фікстури для тестів.

Кожен тест отримує ІЗОЛЬОВАНУ in-memory SQLite-базу: таблиці створюються
перед тестом і видаляються після. Завдяки StaticPool усі зʼєднання в межах
одного тесту бачать ту саму базу, тож дані зберігаються між запитами в межах
тесту, але не протікають між тестами.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def db_session():
    """Свіжа in-memory база для кожного тесту."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    """TestClient з підміненою залежністю get_db на тестову сесію."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Зразок даних користувача."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }


@pytest.fixture
def auth_headers(client, sample_user_data):
    """Заголовки авторизації: реєструє користувача та логіниться."""
    client.post("/auth/register", json=sample_user_data)

    response = client.post("/auth/login", data={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"],
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
