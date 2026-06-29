"""
Prometheus-метрики HTTP-запитів.

Лейбли беруться з ШАБЛОНУ маршруту (напр. /favorites/{favorite_id}), а не з
конкретного URL — інакше кардинальність метрик вибухне через id у шляху.
"""
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Кількість HTTP-запитів",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Тривалість обробки HTTP-запиту",
    ["method", "path"],
)


def _route_template(request: Request) -> str:
    """Шаблон маршруту для запиту (низька кардинальність) або 'unknown'."""
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return getattr(route, "path", request.url.path)
    return "unknown"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Інкрементує лічильники та гістограму тривалості для кожного запиту."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = _route_template(request)
        with REQUEST_LATENCY.labels(request.method, path).time():
            response = await call_next(request)
        REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
        return response


def render_metrics() -> Response:
    """Відповідь у форматі Prometheus exposition."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
