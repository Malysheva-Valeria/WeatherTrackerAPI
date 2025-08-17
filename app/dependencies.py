"""
FastAPI Dependencies для WeatherTracker API
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.api.models import User


def get_current_user_dependency():
    """
    Dependency для отримання поточного користувача
    """
    # TODO: Реалізувати після створення JWT системи
    pass


def get_db_session() -> Session:
    """
    Dependency для отримання сесії бази даних
    Alias для get_db() для зручності
    """
    return Depends(get_db)


def validate_user_exists(user_id: int, db: Session = Depends(get_db)) -> User:
    """
    Dependency для перевірки існування користувача
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user


def validate_active_user(user: User = Depends(validate_user_exists)) -> User:
    """
    Dependency для перевірки що користувач активний
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not active"
        )
    return user