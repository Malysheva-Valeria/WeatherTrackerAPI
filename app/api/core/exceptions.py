"""
Централізована обробка помилок: єдиний формат JSON-відповіді з request_id.

Кожна помилка повертає `{"detail": ..., "request_id": ...}`, що дозволяє
користувачу/підтримці послатися на конкретний запит у логах.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Базовий виняток застосунку з HTTP-статусом і повідомленням."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_response(status_code: int, detail, request: Request, headers=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"detail": detail, "request_id": _request_id(request)}),
        headers=headers,
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return _error_response(exc.status_code, exc.detail, request)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(exc.status_code, exc.detail, request, headers=getattr(exc, "headers", None))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(422, exc.errors(), request)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Необроблена помилка [%s]", _request_id(request))
    return _error_response(500, "Внутрішня помилка сервера", request)


def register_exception_handlers(app: FastAPI) -> None:
    """Реєструє всі обробники винятків на застосунку."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
