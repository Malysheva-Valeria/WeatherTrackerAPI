"""
Ініціалізація моделей WeatherTracker API
"""
from app.api.models.base import BaseModel
from app.api.models.user import User

# Експорт всіх моделей для зручності імпорту
__all__ = [
    "BaseModel",
    "User"
]