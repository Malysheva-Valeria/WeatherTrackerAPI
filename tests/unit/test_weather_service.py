"""Unit тести для WeatherService"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from app.api.services.weather_service import WeatherService
from app.api.models.weather_request import WeatherRequest


class TestWeatherService:
    """Unit тести для WeatherService"""

    @pytest.fixture
    def weather_service(self):
        """Фікстура WeatherService"""
        return WeatherService()

    @pytest.fixture
    def mock_db(self):
        """Мок бази даних"""
        return Mock()

    @pytest.fixture
    def mock_openweather_response(self):
        """Мок відповіді OpenWeather API"""
        return {
            "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
            "main": {
                "temp": 20.5,
                "feels_like": 22.1,
                "temp_min": 18.0,
                "temp_max": 23.0,
                "pressure": 1013,
                "humidity": 65
            },
            "wind": {"speed": 3.5, "deg": 180},
            "sys": {"country": "UA", "sunrise": 1634523600, "sunset": 1634564400},
            "name": "Kyiv",
            "id": 703448,
            "coord": {"lat": 50.4501, "lon": 30.5234}
        }

    @pytest.fixture
    def mock_forecast_response(self):
        """Мок відповіді прогнозу OpenWeather API"""
        return {
            "city": {
                "id": 703448,
                "name": "Kyiv",
                "country": "UA",
                "coord": {"lat": 50.4501, "lon": 30.5234}
            },
            "cnt": 40,
            "list": [
                {
                    "dt": 1634550000,
                    "main": {
                        "temp": 15.2,
                        "feels_like": 14.8,
                        "temp_min": 12.1,
                        "temp_max": 15.2,
                        "pressure": 1018,
                        "humidity": 72
                    },
                    "weather": [{"main": "Clouds", "description": "broken clouds", "icon": "04d"}],
                    "wind": {"speed": 2.1, "deg": 220},
                    "dt_txt": "2025-08-21 12:00:00"
                }
            ]
        }

    @patch('httpx.AsyncClient.get')
    async def test_get_current_weather_success(self, mock_get, weather_service, mock_db, mock_openweather_response):
        """Тест успішного отримання поточної погоди"""
        # Налаштування мока API відповіді
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openweather_response
        mock_get.return_value = mock_response

        # Виклик методу
        result = await weather_service.get_current_weather(mock_db, "Kyiv", user_id=1)

        # Перевірки
        assert result is not None
        assert result['city'] == "Kyiv"
        assert result['country'] == "UA"
        assert result['temperature'] == 20.5
        assert result['feels_like'] == 22.1
        assert result['humidity'] == 65
        assert result['pressure'] == 1013
        assert result['wind_speed'] == 3.5
        assert result['condition'] == "Clear"
        assert result['description'] == "clear sky"
        assert result['mock'] is False

        # Перевірка виклику API
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    async def test_get_current_weather_api_error(self, mock_get, weather_service, mock_db):
        """Тест обробки помилки API та fallback на mock дані"""
        # Налаштування мока для помилки API
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Виклик методу
        result = await weather_service.get_current_weather(mock_db, "UnknownCity", user_id=1)

        # Перевірки mock даних
        assert result is not None
        assert result['mock'] is True
        assert 'temperature' in result
        assert 'city' in result

    @patch('httpx.AsyncClient.get')
    async def test_get_current_weather_by_coordinates(self, mock_get, weather_service, mock_db,
                                                      mock_openweather_response):
        """Тест отримання погоди за координатами"""
        # Налаштування мока
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openweather_response
        mock_get.return_value = mock_response

        # Виклик методу
        result = await weather_service.get_current_weather_by_coordinates(mock_db, 50.4501, 30.5234, user_id=1)

        # Перевірки
        assert result is not None
        assert result['city'] == "Kyiv"
        assert result['mock'] is False
        assert result['latitude'] == 50.4501
        assert result['longitude'] == 30.5234

    def test_coordinates_validation(self, weather_service):
        """Тест валідації координат"""
        # Валідні координати
        assert weather_service._validate_coordinates(50.4501, 30.5234) is True
        assert weather_service._validate_coordinates(0, 0) is True
        assert weather_service._validate_coordinates(-90, -180) is True
        assert weather_service._validate_coordinates(90, 180) is True

        # Невалідні координати
        assert weather_service._validate_coordinates(91, 30) is False  # lat > 90
        assert weather_service._validate_coordinates(-91, 30) is False  # lat < -90
        assert weather_service._validate_coordinates(50, 181) is False  # lon > 180
        assert weather_service._validate_coordinates(50, -181) is False  # lon < -180

    @patch('httpx.AsyncClient.get')
    async def test_get_weather_forecast_success(self, mock_get, weather_service, mock_db, mock_forecast_response):
        """Тест успішного отримання прогнозу погоди"""
        # Налаштування мока
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_forecast_response
        mock_get.return_value = mock_response

        # Виклик методу
        result = await weather_service.get_weather_forecast(mock_db, "Kyiv", user_id=1)

        # Перевірки
        assert result is not None
        assert result['city'] == "Kyiv"
        assert 'daily_forecasts' in result
        assert len(result['daily_forecasts']) > 0
        assert result['mock'] is False

    def test_save_weather_request(self, weather_service, mock_db):
        """Тест збереження запиту погоди"""
        # Мок моделі WeatherRequest
        with patch('app.api.services.weather_service.WeatherRequest') as MockWeatherRequest:
            mock_request = Mock()
            MockWeatherRequest.return_value = mock_request

            # Виклик методу
            weather_service.save_weather_request(
                db=mock_db,
                user_id=1,
                city="Kyiv",
                request_type="current",
                response_data={"temperature": 20.5}
            )

            # Перевірки
            MockWeatherRequest.assert_called_once()
            mock_db.add.assert_called_once_with(mock_request)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_request)

    def test_get_weather_history(self, weather_service, mock_db):
        """Тест отримання історії запитів погоди"""
        # Налаштування мока
        mock_requests = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_requests

        # Виклик методу
        result = weather_service.get_weather_history(mock_db, user_id=1, skip=0, limit=10)

        # Перевірки
        assert result == mock_requests
        mock_db.query.assert_called()

    def test_delete_weather_request(self, weather_service, mock_db):
        """Тест видалення запиту погоди"""
        # Налаштування мока
        mock_request = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_request

        # Виклик методу
        result = weather_service.delete_weather_request(mock_db, request_id=1, user_id=1)

        # Перевірки
        assert result is True
        mock_db.delete.assert_called_once_with(mock_request)
        mock_db.commit.assert_called_once()

    def test_delete_weather_request_not_found(self, weather_service, mock_db):
        """Тест видалення неіснуючого запиту"""
        # Запит не знайдений
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Виклик методу
        result = weather_service.delete_weather_request(mock_db, request_id=999, user_id=1)

        # Перевірки
        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_get_user_statistics(self, weather_service, mock_db):
        """Тест отримання статистики користувача"""
        # Мок статистики
        mock_db.query.return_value.filter.return_value.count.return_value = 25
        mock_db.query.return_value.filter.return_value.distinct.return_value.count.return_value = 5

        # Виклик методу
        result = weather_service.get_user_statistics(mock_db, user_id=1)

        # Перевірки
        assert 'total_requests' in result
        assert 'unique_cities' in result
        assert result['total_requests'] >= 0
        assert result['unique_cities'] >= 0


@pytest.fixture
def sample_weather_data():
    """Зразок даних погоди для тестів"""
    return {
        "city": "Kyiv",
        "country": "UA",
        "temperature": 20.5,
        "feels_like": 22.1,
        "humidity": 65,
        "pressure": 1013,
        "wind_speed": 3.5,
        "wind_direction": 180,
        "condition": "Clear",
        "description": "clear sky",
        "icon": "01d",
        "latitude": 50.4501,
        "longitude": 30.5234,
        "mock": False,
        "cached": False,
        "request_time": datetime.utcnow().isoformat()
    }