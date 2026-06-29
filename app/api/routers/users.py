"""
Users Router для WeatherTracker API

Ендпойнти для:
- Управління профілем користувача
- Оновлення інформації
- Зміни пароля
- Видалення акаунту
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.models.audit import AuditAction
from app.api.models.user import User
from app.api.schemas.audit import AuditLogResponse
from app.api.schemas.base import MessageResponse
from app.api.schemas.user import PasswordChangeRequest, UserResponse, UserUpdate
from app.api.services.audit_service import AuditService, client_ip
from app.api.services.auth_service import get_auth_service
from app.dependencies import get_current_active_user, get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
        current_user: User = Depends(get_current_active_user)
):
    """
    Отримання профілю поточного користувача

    Args:
        current_user: Поточний активний користувач

    Returns:
        UserResponse: Повна інформація про користувача
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Оновлення профілю поточного користувача

    Args:
        user_update: Дані для оновлення
        current_user: Поточний активний користувач
        db: Сесія бази даних

    Returns:
        UserResponse: Оновлена інформація про користувача

    Raises:
        HTTPException: 400 якщо email/username вже використовуються
    """
    # Перевірка унікальності email (якщо змінюється)
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач з таким email вже існує"
            )

    # Перевірка унікальності username (якщо змінюється)
    if user_update.username and user_update.username != current_user.username:
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач з таким username вже існує"
            )

    # Оновлення поля користувача
    update_data = user_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    # Якщо змінюється email - скидається верифікація
    if user_update.email and user_update.email != current_user.email:
        current_user.is_verified = False

    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
        password_data: PasswordChangeRequest,
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Зміна пароля користувача

    Args:
        password_data: Поточний та новий паролі
        current_user: Поточний активний користувач
        db: Сесія бази даних

    Returns:
        MessageResponse: Повідомлення про успішну зміну пароля

    Raises:
        HTTPException: 400 якщо поточний пароль невірний або новий пароль слабкий
    """
    auth_service = get_auth_service()

    # Перевірка поточного пароля
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поточний пароль невірний"
        )

    # Перевірка сили нового пароля
    is_strong, message = auth_service.validate_password_strength(password_data.new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    # Перевірка що новий пароль відрізняється від поточного
    if auth_service.verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новий пароль має відрізнятись від поточного"
        )

    # Оновлення пароля
    current_user.hashed_password = auth_service.get_password_hash(password_data.new_password)
    db.commit()

    AuditService(db).record(
        AuditAction.PASSWORD_CHANGED, user_id=current_user.id, ip_address=client_ip(request)
    )

    return MessageResponse(message="Пароль успішно змінено")


@router.delete("/me", response_model=MessageResponse)
async def delete_my_account(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Видалення акаунту користувача

    Args:
        current_user: Поточний активний користувач
        db: Сесія бази даних

    Returns:
        MessageResponse: Повідомлення про видалення акаунту
    """
    user_id = current_user.id
    # Замість фізичного видалення - деактивація користувача
    current_user.is_active = False
    db.commit()

    AuditService(db).record(
        AuditAction.ACCOUNT_DEACTIVATED, user_id=user_id, ip_address=client_ip(request)
    )

    return MessageResponse(message="Акаунт успішно деактивовано")


@router.get("/me/audit", response_model=List[AuditLogResponse])
async def get_my_audit_log(
        limit: int = 50,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Журнал аудиту поточного користувача (останні події безпеки).

    Args:
        limit: Максимальна кількість записів (за замовчуванням 50)

    Returns:
        List[AuditLogResponse]: Події у зворотному хронологічному порядку
    """
    limit = max(1, min(limit, 200))
    entries = AuditService(db).list_for_user(current_user.id, limit=limit)
    return [AuditLogResponse.model_validate(e) for e in entries]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Отримання інформації про користувача за ID

    Args:
        user_id: ID користувача
        db: Сесія бази даних
        current_user: Поточний активний користувач

    Returns:
        UserResponse: Публічна інформація про користувача

    Raises:
        HTTPException: 404 якщо користувач не знайдений
    """
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Користувача не знайдено"
        )

    return UserResponse.model_validate(user)
