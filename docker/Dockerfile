# WeatherTracker API — production image
FROM python:3.11-slim AS base

# Системні налаштування Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Системні залежності (libpq для psycopg2, curl для healthcheck)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Спочатку залежності — кращий кеш шарів
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Код застосунку та міграції
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Непривілейований користувач
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
