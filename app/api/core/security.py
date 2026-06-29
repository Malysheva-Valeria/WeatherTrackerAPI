"""
Security middleware: безпекові HTTP-заголовки на всіх відповідях.
"""
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Заголовки, що знижують ризик MIME-sniffing, clickjacking тощо
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "X-XSS-Protection": "0",  # сучасні браузери: вимкнути застарілий аудитор
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Додає безпекові заголовки до кожної відповіді."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response
