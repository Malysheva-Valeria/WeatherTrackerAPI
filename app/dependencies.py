"""
FastAPI Dependencies для WeatherTracker API

Містить всі dependencies для:
- Підключення до бази даних
- JWT аутентифікації
- Перевірки прав доступу
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.api.services.auth_service import get_auth_service
from app.api.models.user import User

# HTTP Bearer scheme для JWT токенів
security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для отримання сесії бази даних

    Yields:
        Session: Сесія SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """
    Dependency для отримання поточного користувача з JWT токену

    Args:
        credentials: HTTP Authorization credentials
        db: Сесія бази даних

    Returns:
        User: Поточний користувач

    Raises:
        HTTPException: Якщо токен невалідний або користувач не знайдений
    """
    # Отримуємо токен з headers
    token = credentials.credentials

    # Перевіряємо токен та отримуємо користувача
    auth_service = get_auth_service()
    user = auth_service.get_user_by_token(db, token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалідний токен аутентифікації",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency для отримання поточного активного користувача

    Args:
        current_user: Поточний користувач

    Returns:
        User: Активний користувач

    Raises:
        HTTPException: Якщо користувач неактивний
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Користувач неактивний"
        )
    return current_user


def get_current_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency для отримання поточного верифікованого користувача

    Args:
        current_user: Поточний активний користувач

    Returns:
        User: Верифікований користувач

    Raises:
        HTTPException: Якщо користувач не верифікований
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Користувач не верифікований. Перевірте email та підтвердіть акаунт."
        )
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency для отримання поточного суперкористувача

    Args:
        current_user: Поточний активний користувач

    Returns:
        User: Суперкористувач

    Raises:
        HTTPException: Якщо користувач не є суперкористувачем
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав доступу"
        )
    return current_user


# Опціональна аутентифікація (для публічних ендпойнтів з додатковими можливостями для авторизованих)
def get_current_user_optional(
        db: Session = Depends(get_db),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Dependency для опціональної аутентифікації

    Args:
        db: Сесія бази даних
        credentials: HTTP Authorization credentials (опціонально)

    Returns:
        Optional[User]: Користувач якщо токен валідний, None якщо токену немає або він невалідний
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        auth_service = get_auth_service()
        user = auth_service.get_user_by_token(db, token)
        return user if user and user.is_active else None
    except Exception:
        return None