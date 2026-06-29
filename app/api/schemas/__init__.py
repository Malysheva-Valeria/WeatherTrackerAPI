"""
Schemas package для WeatherTracker API

Імпорти всіх Pydantic схем
"""

from .auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, Token, TokenData
from .base import BaseSchema, ErrorResponse, MessageResponse, PaginationSchema, TimestampSchema
from .user import PasswordChangeRequest, UserBase, UserCreate, UserResponse, UserSummary, UserUpdate

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
