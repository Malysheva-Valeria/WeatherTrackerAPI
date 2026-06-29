"""
Базові Pydantic схеми для WeatherTracker API

Містить базові класи та загальні схеми для всього API
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Базова схема з налаштуваннями"""
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseSchema):
    """Схема для простих повідомлень"""
    message: str


class ErrorResponse(BaseSchema):
    """Схема для повідомлень про помилки"""
    detail: str
    error_code: Optional[str] = None


class TimestampSchema(BaseSchema):
    """Схема з часовими мітками"""
    created_at: datetime
    updated_at: datetime


class PaginationSchema(BaseSchema):
    """Схема для пагінації"""
    page: int = 1
    size: int = 10
    total: int
    pages: int
