"""
HTTP middleware: трасування запитів (request id) та структуроване логування.
"""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Призначає кожному запиту request_id, логує метод/шлях/статус/тривалість.

    request_id береться із заголовка `X-Request-ID` (якщо прийшов від проксі)
    або генерується. Повертається у відповіді тим самим заголовком — зручно
    корелювати логи між сервісами.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0

        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %s (%.1fms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response
