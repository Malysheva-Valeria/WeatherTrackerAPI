"""
Модель користувача для WeatherTracker API
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.api.models.base import BaseModel


class User(BaseModel):
    """
    Модель користувача
    """
    __tablename__ = "users"

    # Основні поля користувача
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Статус користувача
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Поля активності
    last_login = Column(DateTime, nullable=True)
    login_count = Column(String(10), default="0", nullable=False)

    # Додаткові поля профілю
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)


    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def get_full_name(self):
        """Отримання повного ім'я користувача"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def update_last_login(self):
        """Оновлення часу останнього входу"""
        self.last_login = datetime.utcnow()
        # Збільшити лічильник входів
        try:
            current_count = int(self.login_count)
            self.login_count = str(current_count + 1)
        except (ValueError, TypeError):
            self.login_count = "1"

    def is_authenticated(self):
        """Перевірка чи користувач аутентифікований"""
        return self.is_active and self.is_verified

    def to_dict(self, include_sensitive=False):
        """
        Конвертація в словник з включенням чутливих даних
        """
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_superuser": self.is_superuser,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

        if include_sensitive:
            data["hashed_password"] = self.hashed_password

        return data