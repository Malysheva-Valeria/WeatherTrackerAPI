"""
Schemas package для WeatherTracker API

Імпорти всіх Pydantic схем
"""

from .base import (
    BaseSchema,
    MessageResponse,
    ErrorResponse,
    TimestampSchema,
    PaginationSchema
)

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserSummary,
    PasswordChangeRequest
)

from .auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    LoginResponse,
    RegisterResponse,
    TokenData
)

__all__ = [
    # Base schemas
    "BaseSchema",
    "MessageResponse",
    "ErrorResponse",
    "TimestampSchema",
    "PaginationSchema",

    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserSummary",
    "PasswordChangeRequest",

    # Auth schemas
    "LoginRequest",
    "RegisterRequest",
    "Token",
    "LoginResponse",
    "RegisterResponse",
    "TokenData"
]