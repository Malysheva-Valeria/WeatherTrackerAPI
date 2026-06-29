# WeatherTracker API — типові команди розробки.
# Використання: `make <ціль>` (напр. `make test`).

.DEFAULT_GOAL := help
PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help venv install lint type test check run migrate docker-up docker-down clean

help:  ## Показати цей список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv:  ## Створити віртуальне середовище
	$(PYTHON) -m venv $(VENV)

install: venv  ## Встановити залежності для розробки
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -r requirements-dev.txt

lint:  ## Лінтер (ruff)
	$(BIN)/ruff check app tests

type:  ## Перевірка типів (mypy)
	$(BIN)/mypy app

test:  ## Тести з покриттям
	$(BIN)/pytest

check: lint type test  ## Усі перевірки (як у CI)

run:  ## Запустити dev-сервер з авто-перезавантаженням
	$(BIN)/uvicorn app.main:app --reload

migrate:  ## Застосувати міграції БД
	$(BIN)/alembic upgrade head

docker-up:  ## Підняти dev-стек у Docker
	docker compose -f docker/docker-compose.dev.yml up --build

docker-down:  ## Зупинити dev-стек
	docker compose -f docker/docker-compose.dev.yml down

monitor:  ## Підняти Prometheus + Grafana (моніторинг API на :8000)
	docker compose -f docker/docker-compose.monitoring.yml up -d

clean:  ## Прибрати кеші та артефакти
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
