"""
Authentication Router для WeatherTracker API

Ендпойнти для:
- Реєстрації користувачів
- Логіну та отримання JWT токенів
- Refresh токенів
- Логауту
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.core.rate_limiter import rate_limit
from app.api.models.user import User
from app.api.schemas.auth import LoginResponse, RegisterRequest, RegisterResponse, Token
from app.api.schemas.user import UserResponse
from app.api.services.auth_service import get_auth_service
from app.config import settings
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Спільний ліміт для чутливих ендпоінтів аутентифікації (проти брутфорсу)
_auth_rate_limit = rate_limit(settings.RATE_LIMIT_AUTH_MAX, settings.RATE_LIMIT_AUTH_WINDOW)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_auth_rate_limit],
)
async def register(
        user_data: RegisterRequest,
        db: Session = Depends(get_db)
):
    """
    Реєстрація нового користувача

    Args:
        user_data: Дані для реєстрації (username, email, password)
        db: Сесія бази даних

    Returns:
        RegisterResponse: Інформація про створеного користувача та токен

    Raises:
        HTTPException: 400 якщо користувач вже існує або дані невалідні
    """
    auth_service = get_auth_service()

    # Перевірка сили пароля
    is_strong, message = auth_service.validate_password_strength(user_data.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    # Перевірка чи користувач вже існує
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач з таким email вже існує"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач з таким username вже існує"
            )

    # Створення нового користувача
    hashed_password = auth_service.get_password_hash(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=True,
        is_verified=False  # Треба верифікувати email
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Створення токенів для нового користувача
    tokens = auth_service.create_user_tokens(new_user)

    return RegisterResponse(
        message="Користувач успішно зареєстрований",
        user=UserResponse.model_validate(new_user),
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"]
    )


@router.post("/login", response_model=LoginResponse, dependencies=[_auth_rate_limit])
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    Логін користувача

    Args:
        form_data: Form data з username/email та password
        db: Сесія бази даних

    Returns:
        LoginResponse: JWT токен та інформація про користувача

    Raises:
        HTTPException: 401 якщо credentials невалідні
    """
    auth_service = get_auth_service()

    # Аутентифікація користувача
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний username/email або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Оновлення інформації про логін
    auth_service.update_user_login_info(db, user)

    # Створення токенів
    tokens = auth_service.create_user_tokens(user)

    return LoginResponse(
        message="Успішний вхід в систему",
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Оновлення access токену

    Args:
        db: Сесія бази даних
        current_user: Поточний користувач з токену

    Returns:
        Token: Новий access токен
    """
    auth_service = get_auth_service()
    tokens = auth_service.create_user_tokens(current_user)

    return Token(
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"]
    )


@router.post("/logout")
async def logout():
    """
    Логаут користувача

    Returns:
        dict: Повідомлення про успішний логаут
    """
    return {
        "message": "Успішний вихід з системи",
        "detail": "Видаліть токен з клієнтського застосунку"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_user)
):
    """
    Отримання інформації про поточного користувача

    Args:
        current_user: Поточний користувач з JWT токену
        db: Сесія бази даних

    Returns:
        UserResponse: Інформація про користувача
    """
    return UserResponse.model_validate(current_user)
