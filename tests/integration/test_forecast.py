"""
Робочий тест 5-денного прогнозу з form data логіном
"""

import requests
import json
from datetime import datetime


def test_working_forecast():
    """Тестування з правильним form data логіном"""

    print("🌤️ РОБОЧИЙ ТЕСТ 5-ДЕННОГО ПРОГНОЗУ")
    print("=" * 50)

    try:
        # КРОК 1: Логін через form data (який працює!)
        print("🔐 Логін через form data...")
        login_response = requests.post(
            'http://127.0.0.1:8000/auth/login',
            data={"username": "testuser", "password": "testpass123"},  # data, не json!
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        print(f"📊 Статус логіну: {login_response.status_code}")

        if login_response.status_code != 200:
            print(f"❌ Помилка логіну: {login_response.text}")
            return

        login_data = login_response.json()
        token = login_data['access_token']
        print(f"✅ Токен отримано: {token[:30]}...")
        print(f"👤 Користувач: {login_data.get('user', {}).get('username', 'невідомий')}")

        # КРОК 2: 5-денний прогноз
        print(f"\n🌤️ Запитуємо 5-денний прогноз для Kyiv...")
        forecast_response = requests.get(
            'http://127.0.0.1:8000/weather/forecast',
            params={'city': 'Kyiv'},
            headers={'Authorization': f'Bearer {token}'},
            timeout=30
        )

        print(f"📊 Статус прогнозу: {forecast_response.status_code}")

        if forecast_response.status_code == 200:
            data = forecast_response.json()

            print("🎉 5-ДЕННИЙ ПРОГНОЗ ПРАЦЮЄ ІДЕАЛЬНО!")
            print(f"🏙️ Місто: {data['city']}, {data.get('country', 'невідомо')}")
            print(f"📅 Днів прогнозу: {len(data['daily_forecasts'])}")
            print(f"🤖 Mock дані: {data['mock']}")
            print(f"🔄 Кешовано: {data['cached']}")

            # Статистика
            summary = data['summary']
            print(f"\n📊 ЗАГАЛЬНА СТАТИСТИКА:")
            print(f"🌡️ Середня температура: {summary['avg_temperature']}°C")
            print(f"❄️ Мінімальна: {summary['min_temperature']}°C")
            print(f"🔥 Максимальна: {summary['max_temperature']}°C")
            print(f"☀️ Переважна умова: {summary['dominant_condition']}")
            print(f"🌧️ Дощових днів: {summary['rainy_days']}")
            print(f"💧 Всього опадів: {summary['precipitation_total']}мм")

            # Прогноз по днях
            print(f"\n📅 ДЕТАЛЬНИЙ ПРОГНОЗ:")
            for i, day in enumerate(data['daily_forecasts'][:3]):  # Перші 3 дні
                temp = day['temperature']
                weather = day['weather']
                date_str = day['forecast_date']
                print(f"День {i + 1} ({date_str}): {temp['min']}-{temp['max']}°C ({weather['description']})")

                # Додаткові деталі
                if 'atmosphere' in day and day['atmosphere']:
                    atm = day['atmosphere']
                    print(f"    💧 Вологість: {atm.get('humidity', 'н/д')}%, 📊 Тиск: {atm.get('pressure', 'н/д')}hPa")

                if 'wind' in day and day['wind']:
                    wind = day['wind']
                    print(f"    💨 Вітер: {wind.get('speed', 'н/д')}м/с, напрямок {wind.get('direction', 'н/д')}°")

            # Джерело даних
            if not data['mock']:
                print(f"\n🌍 ВИКОРИСТОВУЮТЬСЯ РЕАЛЬНІ ДАНІ OpenWeather!")
                print(f"🔑 API ключ працює!")
            else:
                print(f"\n🧪 Використовуються тестові дані")

            print(f"\n✅ ТЕСТ ПРОЙШОВ УСПІШНО!")
            print(f"🎊 5-ДЕННИЙ ПРОГНОЗ ГОТОВИЙ!")

        elif forecast_response.status_code == 400:
            print(f"❌ 400 Bad Request - проблема з валідацією:")
            try:
                error_detail = forecast_response.json()
                print(json.dumps(error_detail, indent=2, ensure_ascii=False))
            except:
                print(forecast_response.text)

        elif forecast_response.status_code == 401:
            print(f"❌ 401 Unauthorized - проблема з токеном")

        elif forecast_response.status_code == 500:
            print(f"❌ 500 Internal Server Error:")
            print(forecast_response.text)

        else:
            print(f"❌ Несподівана помилка {forecast_response.status_code}:")
            print(forecast_response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Сервер не запущений! Запусти: uvicorn app.main:app --reload")
    except requests.exceptions.Timeout:
        print("❌ Таймаут запиту - API може бути повільним")
    except Exception as e:
        print(f"❌ Несподівана помилка: {e}")


if __name__ == "__main__":
    test_working_forecast()