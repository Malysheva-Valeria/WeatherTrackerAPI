"""
Weather Service для WeatherTracker API
"""

import httpx
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.config import settings
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from app.api.models.forecast_request import ForecastRequest, DailyForecast
from app.api.schemas.forecast import (
    ForecastResponse,
    DailyForecastData,
    TemperatureData,
    WeatherConditionData,
    AtmosphereData,
    WindData,
    PrecipitationData,
    SunData,
    ForecastSummary,
    FeelsLikeData  # Додай цей імпорт
)


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

    async def get_5day_forecast(self, city: str = None, latitude: float = None,
                                longitude: float = None, days: int = 5,
                                user_id: int = None, db: Session = None) -> ForecastResponse:
        """
        Отримати прогноз погоди на кілька днів

        Args:
            city: Назва міста
            latitude: Широта (альтернатива до міста)
            longitude: Довгота (альтернатива до міста)
            days: Кількість днів прогнозу (1-7)
            user_id: ID користувача для збереження в історію
            db: Сесія бази даних

        Returns:
            ForecastResponse: Прогноз на кілька днів
        """
        try:
            # Валідація параметрів
            if not city and (latitude is None or longitude is None):
                raise ValueError("Вкажіть або місто, або координати")

            if days < 1 or days > 7:
                raise ValueError("Кількість днів має бути від 1 до 7")

            # Перевіряємо кеш
            cached_forecast = None
            if db and user_id:
                cached_forecast = self._get_cached_forecast(db, city, latitude, longitude, days, user_id)

            if cached_forecast:
                return self._convert_cached_forecast_to_response(cached_forecast)

            # Отримуємо дані з OpenWeather API
            raw_forecast_data = await self._fetch_forecast_from_api(city, latitude, longitude, days)

            # Форматуємо відповідь
            forecast_response = self._format_forecast_response(raw_forecast_data, days)

            # Зберігаємо в БД
            if db and user_id:
                await self._save_forecast_to_db(db, user_id, forecast_response, raw_forecast_data)

            return forecast_response

        except Exception as e:
            # Fallback на mock дані
            if "Invalid API key" in str(e) or "api.openweathermap.org" in str(e) or not self.api_key:
                logger.warning(f"Використовуємо mock прогноз для {city or f'{latitude},{longitude}'}")
                return self._generate_mock_forecast(city or f"{latitude},{longitude}", days)
            raise e

    async def _fetch_forecast_from_api(self, city: str = None, latitude: float = None,
                                       longitude: float = None, days: int = 5) -> dict:
        """Отримати прогноз з OpenWeather API"""

        # Формуємо URL для 5-day forecast API
        if city:
            url = f"{self.base_url}/forecast?q={city}&appid={self.api_key}&units=metric&lang=uk"
        else:
            url = f"{self.base_url}/forecast?lat={latitude}&lon={longitude}&appid={self.api_key}&units=metric&lang=uk"

        # Виконуємо запит
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        # Додаємо метадані
        data['cached'] = False
        data['mock'] = False
        data['request_timestamp'] = datetime.utcnow().isoformat()

        return data

    def _format_forecast_response(self, raw_data: dict, days: int) -> ForecastResponse:
        """Форматувати відповідь прогнозу з OpenWeather API"""

        city_info = raw_data['city']
        forecast_list = raw_data['list']

        # Групуємо прогнози по днях
        daily_forecasts = self._group_forecasts_by_day(forecast_list, days)

        # Створюємо схеми для кожного дня
        daily_forecast_schemas = []
        for day_offset, day_data in enumerate(daily_forecasts):
            daily_schema = self._create_daily_forecast_schema(day_data, day_offset)
            daily_forecast_schemas.append(daily_schema)

        # Створюємо загальну статистику
        summary = self._calculate_forecast_summary(daily_forecasts)

        return ForecastResponse(
            city=city_info['name'],
            country=city_info['country'],
            latitude=city_info['coord']['lat'],
            longitude=city_info['coord']['lon'],
            forecast_days=days,
            request_time=datetime.utcnow(),
            daily_forecasts=daily_forecast_schemas,
            summary=summary,
            cached=raw_data.get('cached', False),
            mock=raw_data.get('mock', False),
            expires_at=datetime.utcnow() + timedelta(hours=1)  # Кеш прогнозу на 1 годину
        )

    def _group_forecasts_by_day(self, forecast_list: List[dict], days: int) -> List[List[dict]]:
        """Групувати прогнози по днях"""

        # Словник для групування по датах
        daily_groups = {}

        for forecast in forecast_list:
            # Отримуємо дату прогнозу
            dt = datetime.fromtimestamp(forecast['dt'])
            date_key = dt.date()

            if date_key not in daily_groups:
                daily_groups[date_key] = []

            daily_groups[date_key].append(forecast)

        # Сортуємо по датах і беремо потрібну кількість днів
        sorted_dates = sorted(daily_groups.keys())
        return [daily_groups[date] for date in sorted_dates[:days]]

    def _create_daily_forecast_schema(self, day_forecasts: List[dict], day_offset: int) -> DailyForecastData:
        """Створити схему для одного дня"""

        # Вибираємо основний прогноз (середина дня)
        main_forecast = day_forecasts[len(day_forecasts) // 2]

        # Рахуємо мін/макс температуру за день
        temps = [f['main']['temp'] for f in day_forecasts]
        feels_like_temps = [f['main']['feels_like'] for f in day_forecasts]

        # Дата прогнозу
        forecast_date = datetime.fromtimestamp(main_forecast['dt']).date()

        return DailyForecastData(
            forecast_date=forecast_date,
            day_offset=day_offset,
            temperature=TemperatureData(
                min=round(min(temps), 1),
                max=round(max(temps), 1),
                avg=round(sum(temps) / len(temps), 1)
            ),
            feels_like=FeelsLikeData(
                min=round(min(feels_like_temps), 1),
                max=round(max(feels_like_temps), 1)
            ),
            weather=WeatherConditionData(
                condition=main_forecast['weather'][0]['main'],
                description=main_forecast['weather'][0]['description'],
                icon=main_forecast['weather'][0]['icon']
            ),
            atmosphere=AtmosphereData(
                humidity=main_forecast['main']['humidity'],
                pressure=main_forecast['main']['pressure'],
                visibility=main_forecast.get('visibility', 10000) / 1000  # м -> км
            ),
            wind=WindData(
                speed=main_forecast['wind']['speed'],
                direction=main_forecast['wind'].get('deg', 0),
                gust=main_forecast['wind'].get('gust')
            ),
            precipitation=PrecipitationData(
                probability=int(main_forecast.get('pop', 0) * 100),  # 0-1 -> 0-100%
                amount=main_forecast.get('rain', {}).get('3h', 0) or main_forecast.get('snow', {}).get('3h', 0)
            )
        )

    def _calculate_forecast_summary(self, daily_forecasts: List[List[dict]]) -> ForecastSummary:
        """Розрахувати загальну статистику прогнозу"""

        all_temps = []
        conditions = []
        total_precipitation = 0
        rainy_days = 0

        for day_forecasts in daily_forecasts:
            # Температури
            day_temps = [f['main']['temp'] for f in day_forecasts]
            all_temps.extend(day_temps)

            # Умови погоди
            main_condition = day_forecasts[0]['weather'][0]['main']
            conditions.append(main_condition)

            # Опади
            day_precipitation = sum(
                f.get('rain', {}).get('3h', 0) + f.get('snow', {}).get('3h', 0)
                for f in day_forecasts
            )
            total_precipitation += day_precipitation

            if day_precipitation > 0:
                rainy_days += 1

        # Найчастіша умова
        dominant_condition = max(set(conditions), key=conditions.count) if conditions else "Clear"

        return ForecastSummary(
            avg_temperature=round(sum(all_temps) / len(all_temps), 1) if all_temps else 0,
            min_temperature=round(min(all_temps), 1) if all_temps else 0,
            max_temperature=round(max(all_temps), 1) if all_temps else 0,
            dominant_condition=dominant_condition,
            rainy_days=rainy_days,
            precipitation_total=round(total_precipitation, 1)
        )

    def _generate_mock_forecast(self, location: str, days: int) -> ForecastResponse:
        """Генерувати mock прогноз для тестування"""

        daily_forecasts = []
        base_temp = 18.0

        for day_offset in range(days):
            forecast_date = date.today() + timedelta(days=day_offset)

            # Варіація температури
            temp_variation = (day_offset - days // 2) * 2
            min_temp = base_temp + temp_variation - 3
            max_temp = base_temp + temp_variation + 5

            daily_forecast = DailyForecastData(
                forecast_date=forecast_date,
                day_offset=day_offset,
                temperature=TemperatureData(
                    min=round(min_temp, 1),
                    max=round(max_temp, 1),
                    avg=round((min_temp + max_temp) / 2, 1)
                ),
                feels_like=FeelsLikeData(
                    min=round(min_temp - 1, 1),
                    max=round(max_temp + 1, 1)
                ),
                weather=WeatherConditionData(
                    condition="Clear" if day_offset % 2 == 0 else "Clouds",
                    description="ясне небо" if day_offset % 2 == 0 else "хмарно",
                    icon="01d" if day_offset % 2 == 0 else "03d"
                ),
                atmosphere=AtmosphereData(
                    humidity=60 + day_offset * 5,
                    pressure=1013 - day_offset,
                    visibility=10.0
                ),
                wind=WindData(
                    speed=2.0 + day_offset * 0.5,
                    direction=180 + day_offset * 30
                ),
                precipitation=PrecipitationData(
                    probability=10 + day_offset * 10,
                    amount=0.0
                )
            )
            daily_forecasts.append(daily_forecast)

        summary = ForecastSummary(
            avg_temperature=base_temp,
            min_temperature=base_temp - 3,
            max_temperature=base_temp + 5,
            dominant_condition="Clear",
            rainy_days=0,
            precipitation_total=0.0
        )

        return ForecastResponse(
            city=location,
            country="UA",
            latitude=50.4501,
            longitude=30.5234,
            forecast_days=days,
            request_time=datetime.utcnow(),
            daily_forecasts=daily_forecasts,
            summary=summary,
            cached=False,
            mock=True,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

    def _get_cached_forecast(self, db: Session, city: str = None, latitude: float = None,
                             longitude: float = None, days: int = 5, user_id: int = None) -> Optional[ForecastRequest]:
        """Отримати кешований прогноз з БД"""

        # Шукаємо недавній прогноз (останні 1 година)
        cache_time = datetime.utcnow() - timedelta(hours=1)

        query = db.query(ForecastRequest).filter(
            ForecastRequest.user_id == user_id,
            ForecastRequest.forecast_days == days,
            ForecastRequest.request_time >= cache_time
        )

        if city:
            query = query.filter(ForecastRequest.city == city)
        else:
            query = query.filter(
                ForecastRequest.latitude == latitude,
                ForecastRequest.longitude == longitude
            )

        return query.order_by(ForecastRequest.request_time.desc()).first()

    def _convert_cached_forecast_to_response(self, cached_forecast: ForecastRequest) -> ForecastResponse:
        """Конвертувати кешований прогноз в відповідь"""

        # Отримуємо daily forecasts
        daily_forecasts = []
        for daily in cached_forecast.daily_forecasts:
            daily_schema = DailyForecastData(
                forecast_date=daily.forecast_date,
                day_offset=daily.day_offset,
                temperature=TemperatureData(
                    min=daily.temperature_min,
                    max=daily.temperature_max,
                    avg=daily.temperature_avg
                ),
                feels_like=FeelsLikeData(
                    min=daily.feels_like_min,
                    max=daily.feels_like_max
                ),
                weather=WeatherConditionData(
                    condition=daily.weather_condition,
                    description=daily.description,
                    icon=daily.icon_code
                ),
                atmosphere=AtmosphereData(
                    humidity=daily.humidity,
                    pressure=daily.pressure,
                    visibility=daily.visibility
                ),
                wind=WindData(
                    speed=daily.wind_speed,
                    direction=daily.wind_direction,
                    gust=daily.wind_gust
                ),
                precipitation=PrecipitationData(
                    probability=daily.precipitation_probability,
                    amount=daily.precipitation_amount
                )
            )
            daily_forecasts.append(daily_schema)

        summary = ForecastSummary(
            avg_temperature=cached_forecast.avg_temperature,
            min_temperature=cached_forecast.min_temperature,
            max_temperature=cached_forecast.max_temperature,
            dominant_condition="Clear",  # Можна розрахувати з daily forecasts
            rainy_days=0,  # Можна розрахувати з daily forecasts
            precipitation_total=0.0  # Можна розрахувати з daily forecasts
        )

        return ForecastResponse(
            city=cached_forecast.city,
            country=cached_forecast.country,
            latitude=cached_forecast.latitude,
            longitude=cached_forecast.longitude,
            forecast_days=cached_forecast.forecast_days,
            request_time=cached_forecast.request_time,
            daily_forecasts=daily_forecasts,
            summary=summary,
            cached=True,
            mock=cached_forecast.is_mock,
            expires_at=cached_forecast.cache_expires_at
        )

    async def _save_forecast_to_db(self, db: Session, user_id: int, forecast_response: ForecastResponse,
                                   raw_data: dict):
        """Зберегти прогноз в базу даних"""

        try:
            # Створюємо основний запис прогнозу
            forecast_request = ForecastRequest(
                user_id=user_id,
                city=forecast_response.city,
                country=forecast_response.country,
                latitude=forecast_response.latitude,
                longitude=forecast_response.longitude,
                forecast_days=forecast_response.forecast_days,
                request_time=forecast_response.request_time,
                is_cached=forecast_response.cached,
                is_mock=forecast_response.mock,
                cache_expires_at=forecast_response.expires_at,
                forecast_data=raw_data,
                avg_temperature=forecast_response.summary.avg_temperature,
                min_temperature=forecast_response.summary.min_temperature,
                max_temperature=forecast_response.summary.max_temperature
            )

            db.add(forecast_request)
            db.flush()  # Отримуємо ID

            # Створюємо записи для кожного дня
            for daily_forecast in forecast_response.daily_forecasts:
                daily_record = DailyForecast(
                    forecast_request_id=forecast_request.id,
                    forecast_date=daily_forecast.forecast_date,
                    day_offset=daily_forecast.day_offset,
                    temperature_min=daily_forecast.temperature.min,
                    temperature_max=daily_forecast.temperature.max,
                    temperature_avg=daily_forecast.temperature.avg,
                    feels_like_min=daily_forecast.feels_like.min if daily_forecast.feels_like else None,
                    feels_like_max=daily_forecast.feels_like.max if daily_forecast.feels_like else None,
                    weather_condition=daily_forecast.weather.condition,
                    description=daily_forecast.weather.description,
                    icon_code=daily_forecast.weather.icon,
                    humidity=daily_forecast.atmosphere.humidity if daily_forecast.atmosphere else None,
                    pressure=daily_forecast.atmosphere.pressure if daily_forecast.atmosphere else None,
                    visibility=daily_forecast.atmosphere.visibility if daily_forecast.atmosphere else None,
                    wind_speed=daily_forecast.wind.speed if daily_forecast.wind else None,
                    wind_direction=daily_forecast.wind.direction if daily_forecast.wind else None,
                    wind_gust=daily_forecast.wind.gust if daily_forecast.wind else None,
                    precipitation_probability=daily_forecast.precipitation.probability if daily_forecast.precipitation else None,
                    precipitation_amount=daily_forecast.precipitation.amount if daily_forecast.precipitation else None
                )
                db.add(daily_record)

            db.commit()
            logger.info(f"Прогноз для {forecast_response.city} збережено в БД")

        except Exception as e:
            db.rollback()
            logger.error(f"Помилка збереження прогнозу: {e}")

    # Додай ці методи до класу WeatherService в app/api/services/weather_service.py

    async def get_current_weather_by_coordinates(self, latitude: float, longitude: float, use_mock: bool = False) -> \
    Dict[str, Any]:
        """
        Отримання поточної погоди по координатах

        Args:
            latitude: Широта (-90 до 90)
            longitude: Довгота (-180 до 180)
            use_mock: Використовувати mock дані замість API

        Returns:
            Dict з даними про погоду
        """
        # Валідація координат
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Широта має бути від -90 до 90, отримано: {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Довгота має бути від -180 до 180, отримано: {longitude}")

        # Перевірка кешу по координатах
        cache_key = self._get_cache_key(f"lat{latitude}_lon{longitude}", "current")
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info(f"Повертаємо кешовані дані для координат {latitude}, {longitude}")
            return {**self.cache[cache_key]['data'], "cached": True}

        # Якщо використовується mock дані або немає API ключа
        if use_mock or not self.api_key:
            logger.warning(f"Використовуємо mock дані для координат {latitude}, {longitude}")
            mock_data = self._get_mock_weather_by_coordinates(latitude, longitude)

            # Кешування mock даних
            self.cache[cache_key] = {
                'data': mock_data,
                'cached_at': datetime.now()
            }

            return {**mock_data, "cached": False, "mock": True}

        # Запит до OpenWeather API по координатах
        url = f"{self.base_url}/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
            "lang": "uk"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()

                # Додаємо координати для зручності
                data['request_coordinates'] = {
                    'latitude': latitude,
                    'longitude': longitude
                }

                # Кешуємо результат
                self.cache[cache_key] = {
                    'data': data,
                    'cached_at': datetime.now()
                }

                logger.info(f"Отримано дані погоди для координат {latitude}, {longitude}")
                return {**data, "cached": False, "mock": False}

            elif response.status_code == 401:
                logger.error("Недійсний API ключ OpenWeather")
                # Fallback на mock дані
                return await self.get_current_weather_by_coordinates(latitude, longitude, use_mock=True)

            elif response.status_code == 400:
                raise ValueError(f"Невірні координати: {latitude}, {longitude}")

            elif response.status_code == 429:
                raise ValueError("Перевищено ліміт запитів до OpenWeather API")

            else:
                logger.error(f"OpenWeather API помилка: {response.status_code}")
                # Fallback на mock дані
                return await self.get_current_weather_by_coordinates(latitude, longitude, use_mock=True)

        except httpx.TimeoutException:
            logger.error(f"Таймаут запиту для координат {latitude}, {longitude}")
            # Fallback на mock дані
            return await self.get_current_weather_by_coordinates(latitude, longitude, use_mock=True)

        except Exception as e:
            logger.error(f"Несподівана помилка: {e}")
            # Fallback на mock дані
            return await self.get_current_weather_by_coordinates(latitude, longitude, use_mock=True)

    def _get_mock_weather_by_coordinates(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Mock дані для погоди по координатах"""

        # Визначаємо регіон по координатах для більш реалістичних даних
        city_name = self._guess_city_by_coordinates(latitude, longitude)
        country_code = self._guess_country_by_coordinates(latitude, longitude)

        # Базова температура залежно від широти
        base_temp = 20 - abs(latitude) * 0.3  # Холодніше біля полюсів

        return {
            "name": city_name,
            "coord": {
                "lat": latitude,
                "lon": longitude
            },
            "sys": {"country": country_code},
            "main": {
                "temp": round(base_temp + (longitude % 10 - 5), 1),  # Варіація по довготі
                "feels_like": round(base_temp + (longitude % 10 - 5) + 1.5, 1),
                "humidity": max(30, min(90, int(60 + latitude % 30))),
                "pressure": max(980, min(1050, int(1013 + longitude % 40 - 20)))
            },
            "weather": [{
                "main": "Clear" if abs(latitude) < 45 else "Clouds",
                "description": "ясне небо" if abs(latitude) < 45 else "хмарно",
                "icon": "01d" if abs(latitude) < 45 else "03d"
            }],
            "wind": {
                "speed": round(abs(longitude % 10) * 0.5 + 1, 1),
                "deg": int((latitude + longitude) % 360)
            },
            "dt": int(datetime.now().timestamp()),
            "request_coordinates": {
                "latitude": latitude,
                "longitude": longitude
            }
        }

    def _guess_city_by_coordinates(self, latitude: float, longitude: float) -> str:
        """Спрощене визначення міста по координатах для mock даних"""

        # Відомі координати великих міст для більш реалістичних mock даних
        known_cities = [
            (50.4501, 30.5234, "Kyiv"),
            (51.5074, -0.1278, "London"),
            (40.7128, -74.0060, "New York"),
            (-33.8688, 151.2093, "Sydney"),
            (48.8566, 2.3522, "Paris"),
            (55.7558, 37.6176, "Moscow"),
            (35.6762, 139.6503, "Tokyo"),
            (52.5200, 13.4050, "Berlin")
        ]

        # Знаходимо найближче місто
        min_distance = float('inf')
        closest_city = "Unknown Location"

        for city_lat, city_lon, city_name in known_cities:
            distance = ((latitude - city_lat) ** 2 + (longitude - city_lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_city = city_name

        # Якщо дуже далеко від відомих міст, генеруємо назву
        if min_distance > 10:  # Більше ~10 градусів
            return f"Location {latitude:.2f}, {longitude:.2f}"

        return closest_city

    def _guess_country_by_coordinates(self, latitude: float, longitude: float) -> str:
        """Спрощене визначення країни по координатах"""

        # Спрощена логіка визначення регіону
        if 40 <= latitude <= 70 and 20 <= longitude <= 180:
            return "UA"  # Східна Європа
        elif 45 <= latitude <= 70 and -10 <= longitude <= 30:
            return "GB"  # Західна Європа
        elif 25 <= latitude <= 50 and -130 <= longitude <= -60:
            return "US"  # Північна Америка
        elif -45 <= latitude <= -10 and 110 <= longitude <= 180:
            return "AU"  # Австралія
        else:
            return "XX"  # Невідома країна


# Глобальний екземпляр сервісу
weather_service = WeatherService()


def get_weather_service() -> WeatherService:
    """
    Отримання екземпляру сервісу погоди

    Returns:
        WeatherService: Екземпляр сервісу погоди
    """
    return weather_service