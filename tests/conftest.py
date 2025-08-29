"""Глобальні фікстури для тестів"""
import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.api.models.user import User

# Тестова база даних в пам'яті
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def test_db():
    """Створення тестової бази даних"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Сесія бази даних для тестів"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """TestClient для API тестів"""

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
    """Зразок даних користувача"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }


@pytest.fixture
def auth_headers(client, sample_user_data):
    """Заголовки авторизації для тестів"""
    # Реєстрація користувача
    client.post("/auth/register", json=sample_user_data)

    # Логін для отримання токена
    response = client.post("/auth/login", data={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"]
    })
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}