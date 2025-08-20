"""
Weather Service для WeatherTracker API
"""

import httpx
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """Сервіс для отримання даних про погоду"""

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = getattr(settings, 'OPENWEATHER_BASE_URL', 'http://api.openweathermap.org/data/2.5')
        self.timeout = 10.0
        self.cache = {}  # Простий in-memory кеш
        self.cache_ttl = 600  # 10 хвилин

    def _get_cache_key(self, city: str, request_type: str) -> str:
        """Генерація ключа для кешу"""
        return f"weather:{city.lower()}:{request_type}"

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Перевірка чи кеш ще валідний"""
        if not cache_entry:
            return False
        cache_time = cache_entry.get('cached_at')
        if not cache_time:
            return False
        return datetime.now() - cache_time < timedelta(seconds=self.cache_ttl)

    def _get_mock_current_weather(self, city: str) -> Dict[str, Any]:
        """Mock дані для поточної погоди"""
        mock_data = {
            "kyiv": {
                "name": "Kyiv",
                "sys": {"country": "UA"},
                "main": {
                    "temp": 22.5,
                    "feels_like": 23.1,
                    "humidity": 65,
                    "pressure": 1013
                },
                "weather": [{
                    "main": "Clear",
                    "description": "ясне небо",
                    "icon": "01d"
                }],
                "wind": {
                    "speed": 3.2,
                    "deg": 180
                },
                "dt": int(datetime.now().timestamp())
            },
            "london": {
                "name": "London",
                "sys": {"country": "GB"},
                "main": {
                    "temp": 18.5,
                    "feels_like": 17.8,
                    "humidity": 72,
                    "pressure": 1015
                },
                "weather": [{
                    "main": "Clouds",
                    "description": "хмарно",
                    "icon": "04d"
                }],
                "wind": {
                    "speed": 2.1,
                    "deg": 220
                },
                "dt": int(datetime.now().timestamp())
            }
        }

        # Повернення даних для конкретного міста або загальні для тесту
        city_key = city.lower()
        if city_key in mock_data:
            return mock_data[city_key]
        else:
            # Загальні mock дані для будь-якого міста
            return {
                "name": city.title(),
                "sys": {"country": "XX"},
                "main": {
                    "temp": 20.0,
                    "feels_like": 20.5,
                    "humidity": 60,
                    "pressure": 1010
                },
                "weather": [{
                    "main": "Clear",
                    "description": "ясно",
                    "icon": "01d"
                }],
                "wind": {
                    "speed": 2.5,
                    "deg": 200
                },
                "dt": int(datetime.now().timestamp())
            }

    async def get_current_weather(self, city: str, use_mock: bool = False) -> Dict[str, Any]:
        """
        Отримання поточної погоди для міста

        Args:
            city: Назва міста
            use_mock: Використовувати mock дані замість API

        Returns:
            Dict з даними про погоду
        """
        # Перевірка кешу
        cache_key = self._get_cache_key(city, "current")
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info(f"Повертаємо кешовані дані для {city}")
            return {**self.cache[cache_key]['data'], "cached": True}

        # Якщо використовується mock дані або немає API ключа
        if use_mock or not self.api_key:
            logger.warning(f"Використовуємо mock дані для {city}")
            mock_data = self._get_mock_current_weather(city)

            # Кешування mock даних
            self.cache[cache_key] = {
                'data': mock_data,
                'cached_at': datetime.now()
            }

            return {**mock_data, "cached": False, "mock": True}

        # Запит до OpenWeather API
        url = f"{self.base_url}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": "uk"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()

                # Кешуємо результат
                self.cache[cache_key] = {
                    'data': data,
                    'cached_at': datetime.now()
                }

                logger.info(f"Отримано дані погоди для {city}")
                return {**data, "cached": False, "mock": False}

            elif response.status_code == 401:
                logger.error("Недійсний API ключ OpenWeather")
                # Fallback на mock дані
                return await self.get_current_weather(city, use_mock=True)

            elif response.status_code == 404:
                raise ValueError(f"Місто '{city}' не знайдено")

            elif response.status_code == 429:
                raise ValueError("Перевищено ліміт запитів до OpenWeather API")

            else:
                logger.error(f"OpenWeather API помилка: {response.status_code}")
                # Fallback на mock дані
                return await self.get_current_weather(city, use_mock=True)

        except httpx.TimeoutException:
            logger.error(f"Таймаут запиту для {city}")
            # Fallback на mock дані
            return await self.get_current_weather(city, use_mock=True)

        except Exception as e:
            logger.error(f"Несподівана помилка: {e}")
            # Fallback на mock дані
            return await self.get_current_weather(city, use_mock=True)

    def format_weather_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Форматування відповіді погоди в стандартний формат

        Args:
            raw_data: Сирі дані з API або mock

        Returns:
            Форматовані дані
        """
        return {
            "city": raw_data.get("name", "Unknown"),
            "country": raw_data.get("sys", {}).get("country", "Unknown"),
            "temperature": raw_data.get("main", {}).get("temp"),
            "feels_like": raw_data.get("main", {}).get("feels_like"),
            "description": raw_data.get("weather", [{}])[0].get("description", ""),
            "condition": raw_data.get("weather", [{}])[0].get("main", ""),
            "humidity": raw_data.get("main", {}).get("humidity"),
            "pressure": raw_data.get("main", {}).get("pressure"),
            "wind_speed": raw_data.get("wind", {}).get("speed"),
            "wind_direction": raw_data.get("wind", {}).get("deg"),
            "timestamp": datetime.fromtimestamp(raw_data.get("dt", datetime.now().timestamp())),
            "cached": raw_data.get("cached", False),
            "mock": raw_data.get("mock", False)
        }


# Глобальний екземпляр сервісу
weather_service = WeatherService()


def get_weather_service() -> WeatherService:
    """
    Отримання екземпляру сервісу погоди

    Returns:
        WeatherService: Екземпляр сервісу погоди
    """
    return weather_service