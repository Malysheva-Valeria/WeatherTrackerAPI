"""
User Pydantic схеми для WeatherTracker API

Схеми для роботи з користувачами
"""

from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.api.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """Базова схема користувача"""
    username: str = Field(..., min_length=3, max_length=50, description="Ім'я користувача")
    email: EmailStr = Field(..., description="Email адреса")
    first_name: Optional[str] = Field(None, max_length=50, description="Ім'я")
    last_name: Optional[str] = Field(None, max_length=50, description="Прізвище")


class UserCreate(UserBase):
    """Схема для створення користувача"""
    password: str = Field(..., min_length=8, max_length=128, description="Пароль")


class UserUpdate(BaseSchema):
    """Схема для оновлення користувача"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)


class UserResponse(UserBase):
    """Схема для відповіді з інформацією про користувача"""
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool = False
    full_name: str
    login_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseSchema):
    """Коротка інформація про користувача"""
    id: int
    username: str
    full_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeRequest(BaseSchema):
    """Схема для зміни паролю"""
    current_password: str = Field(..., description="Поточний пароль")
    new_password: str = Field(..., min_length=8, max_length=128, description="Новий пароль")