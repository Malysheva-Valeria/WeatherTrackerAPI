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
- **Аутентифікація**: JWT токени
- **Зовнішнє API**: OpenWeatherMap
- **Тестування**: pytest
- **Кешування**: Redis (планується)
- **Контейнеризація**: Docker + docker-compose (планується)

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

## 📚 API Документація

Після запуску сервера документація доступна за адресами:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Основні ендпойнти (планується)

#### Аутентифікація
- `POST /auth/register` - Реєстрація користувача
- `POST /auth/login` - Авторизація користувача

#### Користувачі
- `GET /users/me` - Отримання профілю поточного користувача

#### Погода
- `GET /weather/current?city=Kyiv` - Поточна погода для міста
- `GET /weather/forecast?city=Kyiv` - Прогноз на 5 днів

#### Історія
- `GET /history` - Історія запитів користувача
- `DELETE /history/{id}` - Видалення запису з історії

## 🧪 Тестування

```bash
# Запуск всіх тестів
pytest

# Запуск з покриттям коду
pytest --cov=app

# Запуск конкретного тестового файлу
pytest tests/test_auth_service.py -v
```

## 🔧 Розробка

### Структура проекту
```
weathertracker/
├── app/
│   ├── main.py              # Точка входу FastAPI
│   ├── config.py            # Конфігурація
│   ├── models/              # SQLAlchemy моделі
│   ├── schemas/             # Pydantic схеми
│   ├── routers/             # API роутери
│   ├── services/            # Бізнес логіка
│   └── utils/               # Допоміжні функції
├── tests/                   # Тести
├── alembic/                 # Міграції БД
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
- [ ] **Тиждень 2**: Інтеграція з OpenWeather API
- [ ] **Тиждень 3**: Історія запитів, кешування
- [ ] **Тиждень 4**: Тестування, Docker, розгортання

## 🤝 Співпраця

Ласкаво просимо до внеску в проект! Будь ласка, ознайомтесь з правилами співпраці в файлі CONTRIBUTING.md.

## 📄 Ліцензія

Цей проект розповсюджується під ліцензією MIT. Дивіться файл LICENSE для деталей.

## 📞 Контакти

- **Автор**: Ваше ім'я
- **Email**: your.email@example.com
- **GitHub**: [@yourusername](https://github.com/yourusername)

---

**Статус розробки**: 🚧 В активній розробці

**Версія**: 1.0.0# Test commit
