"""
Authentication Pydantic схеми для WeatherTracker API

Схеми для аутентифікації та авторизації
"""

from typing import Optional

from pydantic import EmailStr, Field

from app.api.schemas.base import BaseSchema
from app.api.schemas.user import UserResponse


class LoginRequest(BaseSchema):
    """Схема для запиту логіну"""
    username: str = Field(..., description="Username або email")
    password: str = Field(..., description="Пароль")


class RegisterRequest(BaseSchema):
    """Схема для запиту реєстрації"""
    username: str = Field(..., min_length=3, max_length=50, description="Ім'я користувача")
    email: EmailStr = Field(..., description="Email адреса")
    password: str = Field(..., min_length=8, max_length=128, description="Пароль")
    first_name: Optional[str] = Field(None, max_length=50, description="Ім'я")
    last_name: Optional[str] = Field(None, max_length=50, description="Прізвище")


class Token(BaseSchema):
    """Схема для JWT токену"""
    access_token: str
    refresh_token: str = Field(..., description="Refresh-токен для оновлення доступу")
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Час життя access-токену в секундах")


class RefreshRequest(BaseSchema):
    """Схема запиту на оновлення токена"""
    refresh_token: str = Field(..., description="Дійсний refresh-токен")


class VerifyEmailRequest(BaseSchema):
    """Схема запиту на підтвердження email"""
    token: str = Field(..., description="Токен підтвердження з листа")


class LoginResponse(Token):
    """Схема для відповіді на логін"""
    message: str
    user: UserResponse


class RegisterResponse(Token):
    """Схема для відповіді на реєстрацію"""
    message: str
    user: UserResponse


class TokenData(BaseSchema):
    """Схема для даних з JWT токену"""
    user_id: Optional[int] = None
    username: Optional[str] = None
