# 🌤️ WeatherTracker API

**API сервіс для отримання прогнозу погоди з історією запитів користувачів**

## 📋 Опис проекту

WeatherTracker API дозволяє користувачам:
- 🔐 Реєструватися та авторизуватися
- 🌦️ Отримувати поточну погоду для будь-якого міста
- 📊 Переглядати прогноз погоди на 5 днів
- 📱 Зберігати та переглядати історію своїх запитів
- 🗑️ Видаляти записи з історії

## 🚀 Технології

- **Backend**: Python 3.11+, FastAPI
- **База даних**: PostgreSQL, SQLAlchemy, Alembic
- **Аутентифікація**: JWT (access + refresh-токени з ротацією та відкликанням)
- **Захист**: rate limiting на auth-ендпоінтах (Redis + fallback), audit log подій безпеки
- **Зовнішнє API**: OpenWeatherMap
- **Тестування**: pytest (+ покриття), TestClient
- **Якість коду**: ruff, mypy (CI)
- **Кешування**: Redis
- **Контейнеризація**: Docker + docker-compose

## 🛠️ Встановлення та запуск

### Передумови
- Python 3.11 або новіший
- PostgreSQL
- Git

### Покрокова інструкція

1. **Клонування репозиторію**
```bash
git clone https://github.com/yourusername/weathertracker.git
cd weathertracker
```

2. **Створення віртуального середовища**
```bash
python -m venv venv

# Активація (Windows)
venv\Scripts\activate

# Активація (Mac/Linux)
source venv/bin/activate
```

3. **Встановлення залежностей**
```bash
pip install -r requirements.txt
```

4. **Налаштування змінних середовища**
```bash
# Скопіювати приклад файлу середовища
cp .env.example .env

# Відредагувати .env файл своїми налаштуваннями
```

5. **Налаштування бази даних**
```sql
-- Підключитися до PostgreSQL та створити базу даних
CREATE DATABASE weathertracker;
CREATE USER weather_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE weathertracker TO weather_user;
```

6. **Запуск додатку**
```bash
# Режим розробки з авто-перезавантаженням
uvicorn app.main:app --reload

# Або через Python
python app/main.py
```

7. **Перевірка роботи**
- Відкрити http://127.0.0.1:8000 - головна сторінка
- Відкрити http://127.0.0.1:8000/docs - Swagger UI документація
- Відкрити http://127.0.0.1:8000/redoc - ReDoc документація

## 🐳 Запуск через Docker

```bash
# Dev-режим (live-reload, локальні Postgres + Redis)
docker compose -f docker/docker-compose.dev.yml up --build

# Production-подібний стек (потрібен заданий SECRET_KEY)
SECRET_KEY=$(openssl rand -hex 32) \
docker compose -f docker/docker-compose.yml up -d --build
```

> ⚠️ У `ENVIRONMENT=production` застосунок **не запуститься** з плейсхолдер-`SECRET_KEY`,
> з `DEBUG=true` або з CORS `*` — це навмисний запобіжник у `app/config.py`.

## 📚 API Документація

Після запуску сервера документація доступна за адресами:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Основні ендпойнти

#### Аутентифікація
- `POST /auth/register` - Реєстрація користувача
- `POST /auth/login` - Авторизація користувача
- `POST /auth/refresh` - Оновлення токенів за refresh-токеном (**з ротацією**)
- `POST /auth/logout` - Відкликання refresh-токена
- `POST /auth/verify-email` - Підтвердження email за токеном з листа
- `POST /auth/resend-verification` - Повторна відправка листа підтвердження
- `GET /auth/me` - Поточний користувач

> 🛡️ `/auth/login` і `/auth/register` обмежені rate limiter'ом
> (`RATE_LIMIT_AUTH_MAX` запитів за `RATE_LIMIT_AUTH_WINDOW` секунд на IP) — захист від брутфорсу.

#### Користувачі
- `GET /users/me` - Отримання профілю поточного користувача
- `GET /users/me/audit` - Журнал аудиту (події безпеки користувача)

#### Погода
- `GET /weather/current?city=Kyiv` - Поточна погода для міста
- `GET /weather/forecast?city=Kyiv&days=5` - Прогноз на кілька днів
- `GET /weather/current/coordinates?latitude=..&longitude=..` - Погода за координатами
- `GET /weather/history` - Історія запитів користувача (з пагінацією)
- `DELETE /weather/history/{id}` - Видалення запису з історії
- `GET /weather/stats` - Статистика запитів

#### Улюблені міста
- `POST /favorites` - Додати місто в обране
- `GET /favorites` - Список улюблених міст
- `DELETE /favorites/{id}` - Прибрати з обраного
- `GET /favorites/weather` - Поточна погода по всіх улюблених містах

#### Аналітика
- `GET /api/v1/analytics/summary` - Зведена аналітика
- `GET /api/v1/analytics/cities/popular` - Популярні міста
- `GET /api/v1/analytics/export/csv` - Експорт у CSV

## 🧪 Тестування

```bash
# Запуск усіх тестів (покриття + поріг 60% налаштовані в pytest.ini)
pytest

# Лінтер та перевірка типів
ruff check app tests
mypy app --ignore-missing-imports

# Запуск конкретного файлу
pytest tests/integration/test_api.py -v
```

CI (`.github/workflows/tests.yml`) проганяє ruff + mypy + pytest на кожен push/PR.

### Зручні команди (Makefile)

```bash
make install   # venv + залежності для розробки
make check     # lint + type + test (як у CI)
make run       # dev-сервер з авто-перезавантаженням
make migrate   # застосувати міграції
make docker-up # підняти dev-стек у Docker
```

Опційно — локальні перевірки перед комітом:

```bash
pip install pre-commit && pre-commit install
```

## 🔧 Розробка

### Структура проекту
```
WeatherTrackerAPI/
├── app/
│   ├── main.py              # Точка входу FastAPI (lifespan, CORS, роутери)
│   ├── config.py            # Конфігурація + prod-валідатор безпеки
│   ├── database.py          # Engine, SessionLocal, get_db
│   ├── dependencies.py      # FastAPI-залежності (auth, get_db)
│   └── api/
│       ├── models/          # SQLAlchemy моделі
│       ├── schemas/         # Pydantic схеми
│       ├── routers/         # API роутери (тонкі)
│       ├── services/        # Бізнес-логіка
│       ├── repositories/    # Доступ до БД
│       └── utils/           # Клієнти (OpenWeather, Redis, email)
├── tests/                   # unit + integration (TestClient)
├── alembic/                 # Міграції БД
├── docker/                  # Dockerfile + compose (prod/dev)
└── requirements.txt         # Залежності
```

### Внесення змін
1. Створити нову гілку: `git checkout -b feature/new-feature`
2. Внести зміни та протестувати
3. Зафіксувати зміни: `git commit -m "Add new feature"`
4. Відправити на GitHub: `git push origin feature/new-feature`
5. Створити Pull Request

## 📝 План розробки

- [x] **Тиждень 1**: Базове налаштування, аутентифікація
- [x] **Тиждень 2**: Інтеграція з OpenWeather API
- [x] **Тиждень 3**: Історія запитів, аналітика, кешування
- [x] **Тиждень 4**: Тестування, Docker, CI

