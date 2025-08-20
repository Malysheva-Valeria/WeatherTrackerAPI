"""
Скрипт для тестування WeatherTracker API
"""

import requests
import json
import time
import sys


def test_weather_api():
    """Повний тест WeatherTracker API"""

    print("WeatherTracker API - Повний тест")
    print("=" * 50)

    # Перевірка що сервер запущений
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("Сервер запущений та працює")
        else:
            print(f"Сервер відповідає, але статус: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Сервер не запущений!")
        print("Запуск серверу: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"Помилка підключення до сервера: {e}")
        return False

    print()

    # ТЕСТ 1: Логін
    print("ТЕСТ 1: Аутентифікація")
    print("-" * 30)

    try:
        login_response = requests.post(
            'http://127.0.0.1:8000/auth/login',
            data={'username': 'testuser', 'password': 'testpass123'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )

        print(f"Статус логіну: {login_response.status_code}")

        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data['access_token']
            print(f"Токен отримано: {token[:50]}...")
            print(f"Користувач: {login_data.get('user', {}).get('username', 'невідомий')}")
            print(f"Термін дії: {login_data.get('expires_in', 'невідомо')} секунд")
        else:
            print(f"Помилка логіну: {login_response.text}")
            return False

    except Exception as e:
        print(f"Помилка логіну: {e}")
        return False

    print()

    # ТЕСТ 2: Weather API
    print("ТЕСТ 2: Weather API")
    print("-" * 30)

    try:
        weather_response = requests.get(
            'http://127.0.0.1:8000/weather/current?city=Kyiv',
            headers={'Authorization': f'Bearer {token}'},
            timeout=15
        )

        print(f"Статус Weather API: {weather_response.status_code}")

        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            print("Weather API працює!")
            print("Дані погоди:")
            print(f"  Місто: {weather_data.get('city', 'невідоме')}")
            print(f"  Країна: {weather_data.get('country', 'невідома')}")
            print(f"  Температура: {weather_data.get('temperature', 'невідома')}°C")
            print(f"  Відчувається: {weather_data.get('feels_like', 'невідома')}°C")
            print(f"  Опис: {weather_data.get('description', 'невідомо')}")
            print(f"  Умови: {weather_data.get('condition', 'невідомо')}")
            print(f"  Вологість: {weather_data.get('humidity', 'невідома')}%")
            print(f"  Тиск: {weather_data.get('pressure', 'невідомий')} hPa")
            print(f"  Вітер: {weather_data.get('wind_speed', 'невідомий')} м/с")
            print(f"  Кешовано: {weather_data.get('cached', 'невідомо')}")
            print(f"  Mock дані: {weather_data.get('mock', 'невідомо')}")

            # Перевірка типу даних
            if weather_data.get('mock', True) == False:
                print("\nВИКОРИСТОВУЮТЬСЯ ДАНІ з OpenWeather!")
                print("API ключ працює!")
            else:
                print("\nВикористовуються тестові mock дані")
                print("API ключ може ще активуватися")

        elif weather_response.status_code == 401:
            print("401 Unauthorized - проблема з токеном")
            return False
        elif weather_response.status_code == 403:
            print("403 Forbidden - токен невалідний")
            return False
        else:
            print(f"Помилка {weather_response.status_code}: {weather_response.text}")
            return False

    except Exception as e:
        print(f"Помилка Weather API: {e}")
        return False

    print()

    # ТЕСТ 3: Історія
    print("ТЕСТ 3: Історія запитів")
    print("-" * 30)

    try:
        history_response = requests.get(
            'http://127.0.0.1:8000/weather/history',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )

        print(f"Статус історії: {history_response.status_code}")

        if history_response.status_code == 200:
            history_data = history_response.json()
            print(f"Історія працює!")
            print(f"Записів в історії: {history_data.get('total', 0)}")

            if history_data.get('items'):
                latest = history_data['items'][0]
                print(f"Останній запит: {latest.get('city')} ({latest.get('request_time', 'невідомо')[:19]})")
        else:
            print(f"Помилка історії: {history_response.text}")

    except Exception as e:
        print(f"Помилка історії: {e}")

    print()

    # ТЕСТ 4: Статистика
    print("ТЕСТ 4: Статистика")
    print("-" * 30)

    try:
        stats_response = requests.get(
            'http://127.0.0.1:8000/weather/stats',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )

        print(f"Статус статистики: {stats_response.status_code}")

        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"Статистика працює!")
            print(f"Всього запитів: {stats_data.get('total_requests', 0)}")
            print(f"Унікальних міст: {stats_data.get('unique_cities', 0)}")

            popular = stats_data.get('most_popular_city', {})
            if popular.get('city'):
                print(f"Популярне місто: {popular['city']} ({popular.get('requests_count', 0)} запитів)")
        else:
            print(f"Помилка статистики: {stats_response.text}")

    except Exception as e:
        print(f"Помилка статистики: {e}")

    print("\n" + "=" * 50)
    print("Тестування завершено!")
    print("Swagger UI: http://127.0.0.1:8000/docs")
    print("WeatherTracker API готовий до використання")

    return True


if __name__ == "__main__":
    test_weather_api()