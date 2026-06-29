"""
JWT Authentication Service для WeatherTracker API

Цей модуль містить всю логіку для:
- Створення та верифікації JWT токенів
- Хешування та перевірки паролів
- Аутентифікації користувачів
- Валідації безпеки паролів
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.api.models.refresh_token import RefreshToken
from app.api.models.user import User
from app.config import settings


class AuthService:
    """
    Сервіс для аутентифікації та роботи з JWT токенами

    Надає методи для:
    - Хешування та верифікації паролів
    - Створення та перевірки JWT токенів
    - Аутентифікації користувачів
    - Валідації безпеки
    """

    def __init__(self):
        """Ініціалізація сервісу аутентифікації"""
        # Налаштування для хешування паролів з bcrypt
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Налаштування JWT з конфігурації
        self.SECRET_KEY = settings.SECRET_KEY
        self.ALGORITHM = settings.ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        """Хешує пароль за допомогою bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Перевірка чи збігається пароль з хешем

        Args:
            plain_password: Пароль в відкритому вигляді
            hashed_password: Хешований пароль з бази даних

        Returns:
            bool: True якщо паролі збігаються, False якщо ні
        """
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    def get_password_hash(self, password: str) -> str:
        """
        Хешування пароля з використанням bcrypt

        Args:
            password: Пароль в відкритому вигляді

        Returns:
            str: Хешований пароль
        """
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Створення JWT access token

        Args:
            data: Дані для включення в токен (зазвичай user_id, username)
            expires_delta: Час життя токену

        Returns:
            str: JWT токен
        """
        to_encode = data.copy()

        # Встановлення часу закінчення дії токену
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        # Кодування JWT токену
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """
        Перевірка та декодування JWT токену

        Args:
            token: JWT токен

        Returns:
            dict: Дані з токену або None якщо токен невалідний
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None
        except Exception:
            return None

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        Аутентифікація користувача по username/email та паролю

        Args:
            db: Сесія бази даних
            username: Username або email користувача
            password: Пароль в відкритому вигляді

        Returns:
            User: Об'єкт користувача або None якщо аутентифікація не вдалась
        """
        # Пошук користувача по username або email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        # Перевірка чи користувач існує
        if not user:
            return None

        # Перевірка чи користувач активний
        if not user.is_active:
            return None

        # Перевірка пароля
        if not self.verify_password(password, user.hashed_password):
            return None

        return user

    def get_user_by_token(self, db: Session, token: str) -> Optional[User]:
        """
        Отримання користувача по JWT токену

        Args:
            db: Сесія бази даних
            token: JWT токен

        Returns:
            User: Об'єкт користувача або None якщо токен невалідний
        """
        payload = self.verify_token(token)
        if payload is None:
            return None

        # Отримання user_id з токену
        user_id = payload.get("sub")
        if user_id is None:
            return None

        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return None

        # Пошук користувача в базі даних
        user = db.query(User).filter(User.id == user_id).first()

        # Перевірка чи користувач активний
        if user and not user.is_active:
            return None

        return user

    def create_user_tokens(self, user: User) -> dict:
        """
        Створення токенів для користувача

        Args:
            user: Об'єкт користувача

        Returns:
            dict: Словник з access_token та додатковою інформацією
        """
        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "username": user.username, "email": user.email},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # в секундах
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            }
        }

    def _create_refresh_token(self, db: Session, user: User) -> str:
        """Створює refresh-токен (JWT з jti) і зберігає його запис у БД."""
        jti = uuid.uuid4().hex
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        token = jwt.encode(
            {
                "sub": str(user.id),
                "jti": jti,
                "type": "refresh",
                "exp": expires_at,
                "iat": datetime.now(timezone.utc),
            },
            self.SECRET_KEY,
            algorithm=self.ALGORITHM,
        )
        db.add(RefreshToken(jti=jti, user_id=user.id, expires_at=expires_at))
        db.commit()
        return token

    def issue_tokens(self, db: Session, user: User) -> dict:
        """Видає пару токенів (access + refresh)."""
        tokens = self.create_user_tokens(user)
        tokens["refresh_token"] = self._create_refresh_token(db, user)
        return tokens

    def _decode_refresh(self, token: str) -> Optional[dict]:
        """Декодує refresh-токен і перевіряє його тип."""
        payload = self.verify_token(token)
        if not payload or payload.get("type") != "refresh":
            return None
        return payload

    def _find_token_row(self, db: Session, payload: dict) -> Optional[RefreshToken]:
        jti = payload.get("jti")
        if not jti:
            return None
        return db.query(RefreshToken).filter(RefreshToken.jti == jti).first()

    def rotate_refresh_token(self, db: Session, token: str) -> Optional[dict]:
        """Перевіряє refresh-токен, відкликає його та видає нову пару (ротація)."""
        payload = self._decode_refresh(token)
        if not payload:
            return None

        row = self._find_token_row(db, payload)
        if not row or not row.is_active:
            return None

        user = db.query(User).filter(User.id == row.user_id).first()
        if not user or not user.is_active:
            return None

        # Ротація: старий токен інвалідовано, видаємо нову пару
        row.revoked = True
        db.commit()
        return self.issue_tokens(db, user)

    def revoke_refresh_token(self, db: Session, token: str) -> bool:
        """Відкликає refresh-токен (logout). True, якщо запис знайдено й відкликано."""
        payload = self._decode_refresh(token)
        if not payload:
            return False
        row = self._find_token_row(db, payload)
        if not row:
            return False
        row.revoked = True
        db.commit()
        return True

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Перевірка сили пароля

        Args:
            password: Пароль для перевірки

        Returns:
            Tuple[bool, str]: (True/False, повідомлення про помилку або успіх)
        """
        if len(password) < 8:
            return False, "Пароль має містити мінімум 8 символів"

        if len(password) > 128:
            return False, "Пароль занадто довгий (максимум 128 символів)"

        if not any(c.isdigit() for c in password):
            return False, "Пароль має містити мінімум одну цифру"

        if not any(c.isalpha() for c in password):
            return False, "Пароль має містити мінімум одну літеру"

        if password.lower() in ['password', '12345678', 'qwerty123', 'password123','11111111']:
            return False, "Пароль занадто простий, оберіть більш складний"

        return True, "Пароль відповідає вимогам безпеки"

    def update_user_login_info(self, db: Session, user: User) -> None:
        """
        Оновлення інформації про логін користувача

        Args:
            db: Сесія бази даних
            user: Об'єкт користувача
        """
        user.last_login = datetime.now(timezone.utc)
        user.login_count += 1
        db.commit()
        db.refresh(user)


# Створення глобального екземпляра сервісу
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """
    Отримання екземпляра сервісу аутентифікації

    Returns:
        AuthService: Екземпляр сервісу аутентифікації
    """
    return auth_service
