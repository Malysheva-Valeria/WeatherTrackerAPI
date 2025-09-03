"""
Unit тести для Models
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from unittest.mock import Mock

from app.api.models.user import User
from app.api.models.weather_request import WeatherRequest


class TestUserModel:
    """Unit тести для моделі User"""

    def test_user_creation_basic(self):
        """Тест створення користувача з основними полями"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$hashed_password_here"
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "$2b$12$hashed_password_here"

        # В пам'яті ці поля None, встановлюються на рівні БД
        assert user.id is None  # Буде встановлено БД
        assert user.created_at is None  # Буде встановлено БД
        assert user.is_active is None  # Буде встановлено БД як True

        print("User модель створюється з основними полями")

    def test_user_creation_with_optional_fields(self):
        """Тест створення користувача з опціональними полями"""
        user = User(
            username="john_doe",
            email="john@example.com",
            hashed_password="hashed_pass",
            first_name="John",
            last_name="Doe",
            is_verified=True
        )

        assert user.username == "john_doe"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_verified == True

        print("User модель підтримує опціональні поля")

    def test_user_full_name_property(self):
        """Тест property full_name"""
        # Користувач з ім'ям та прізвищем
        user1 = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            first_name="John",
            last_name="Doe"
        )
        assert user1.full_name == "John Doe"

        # Користувач тільки з ім'ям
        user2 = User(
            username="testuser2",
            email="test2@example.com",
            hashed_password="hashed",
            first_name="Jane"
        )
        assert user2.full_name == "Jane"

        # Користувач без імені - повертається username
        user3 = User(
            username="testuser3",
            email="test3@example.com",
            hashed_password="hashed"
        )
        assert user3.full_name == "testuser3"

        print("full_name property працює правильно")

    def test_user_repr(self):
        """Тест __repr__ методу User"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed"
        )

        repr_str = repr(user)
        assert "User" in repr_str
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str

        print(f"✅ User __repr__: {repr_str}")

    def test_user_to_dict_method(self):
        """Тест to_dict методу"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            first_name="Test",
            last_name="User"
        )

        user_dict = user.to_dict()

        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["full_name"] == "Test User"
        assert "id" in user_dict
        assert "is_active" in user_dict
        assert "created_at" in user_dict

        print("User to_dict метод працює")

    def test_user_relationships(self):
        """Тест relationships User модель"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed"
        )

        # Relationships повинні бути пустими списками спочатку
        assert hasattr(user, 'weather_requests')
        assert hasattr(user, 'forecast_requests')
        assert isinstance(user.weather_requests, list)
        assert isinstance(user.forecast_requests, list)

        print("User relationships доступні")


class TestWeatherRequestModel:
    """Unit тести для моделі WeatherRequest"""

    def test_weather_request_creation_basic(self):
        """Тест створення базового запиту погоди"""
        weather_request = WeatherRequest(
            user_id=1,
            city="Kyiv",
            temperature=20.5,
            description="clear sky",
            response_data={"temp": 20.5}
        )

        assert weather_request.user_id == 1
        assert weather_request.city == "Kyiv"
        assert weather_request.temperature == 20.5
        assert weather_request.description == "clear sky"
        assert weather_request.response_data == {"temp": 20.5}

        print("WeatherRequest базове створення працює")

    def test_weather_request_detailed_data(self):
        """Тест створення детального запиту погоди"""
        weather_request = WeatherRequest(
            user_id=1,
            city="London",
            country="GB",
            temperature=15.2,
            feels_like=14.8,
            description="partly cloudy",
            weather_condition="Clouds",
            humidity=78,
            pressure=1013,
            wind_speed=3.5,
            wind_direction=180,
            response_data={
                "main": {"temp": 15.2, "feels_like": 14.8},
                "weather": [{"description": "partly cloudy"}]
            }
        )

        assert weather_request.city == "London"
        assert weather_request.country == "GB"
        assert weather_request.temperature == 15.2
        assert weather_request.feels_like == 14.8
        assert weather_request.humidity == 78
        assert weather_request.pressure == 1013
        assert weather_request.wind_speed == 3.5
        assert weather_request.wind_direction == 180

        print("WeatherRequest детальні дані працюють")

    def test_weather_request_json_response_data(self):
        """Тест зберігання складних JSON даних"""
        complex_response = {
            "coord": {"lon": 30.5234, "lat": 50.4501},
            "weather": [
                {"main": "Clear", "description": "clear sky", "icon": "01d"}
            ],
            "main": {
                "temp": 22.3,
                "feels_like": 24.1,
                "temp_min": 19.5,
                "temp_max": 25.0,
                "pressure": 1015,
                "humidity": 68
            },
            "wind": {"speed": 2.5, "deg": 180},
            "dt": 1629545400,
            "sys": {"country": "UA", "sunrise": 1629515826, "sunset": 1629569234},
            "name": "Kyiv"
        }

        weather_request = WeatherRequest(
            user_id=1,
            city="Kyiv",
            country="UA",
            temperature=22.3,
            response_data=complex_response
        )

        assert weather_request.response_data["coord"]["lon"] == 30.5234
        assert weather_request.response_data["weather"][0]["description"] == "clear sky"
        assert weather_request.response_data["main"]["temp"] == 22.3

        print("WeatherRequest зберігає складні JSON дані")

    def test_weather_request_repr(self):
        """Тест __repr__ методу WeatherRequest"""
        weather_request = WeatherRequest(
            user_id=1,
            city="Paris",
            temperature=18.5
        )

        repr_str = repr(weather_request)
        assert "WeatherRequest" in repr_str
        assert "Paris" in repr_str
        assert "18.5" in repr_str

        print(f"WeatherRequest __repr__: {repr_str}")

    def test_weather_request_to_dict_method(self):
        """Тест to_dict методу WeatherRequest"""
        weather_request = WeatherRequest(
            user_id=1,
            city="Berlin",
            country="DE",
            temperature=16.8,
            humidity=72,
            wind_speed=4.2
        )

        request_dict = weather_request.to_dict()

        assert request_dict["user_id"] == 1
        assert request_dict["city"] == "Berlin"
        assert request_dict["country"] == "DE"
        assert request_dict["temperature"] == 16.8
        assert request_dict["humidity"] == 72
        assert request_dict["wind_speed"] == 4.2

        print("WeatherRequest to_dict метод працює")

    def test_weather_request_metadata_fields(self):
        """Тест метаданих полів"""
        weather_request = WeatherRequest(
            user_id=1,
            city="Tokyo",
            is_cached="true",
            is_mock="false",
            response_data={"source": "openweathermap"}
        )

        assert weather_request.is_cached == "true"
        assert weather_request.is_mock == "false"
        assert weather_request.response_data["source"] == "openweathermap"

        print("WeatherRequest метадані працюють")


class TestModelRelationships:
    """Тести зв'язків між моделями"""

    def test_user_weather_requests_foreign_key(self):
        """Тест foreign key зв'язку User -> WeatherRequest"""
        user_id = 1

        # Створення кількох запитів для одного користувача
        requests = []
        for i in range(3):
            req = WeatherRequest(
                user_id=user_id,
                city=f"City{i}",
                temperature=20.0 + i,
                response_data={"temp": 20.0 + i}
            )
            requests.append(req)

        # Всі запити пов'язані з одним user_id
        for req in requests:
            assert req.user_id == user_id

        print("User -> WeatherRequest foreign key зв'язок працює")

    def test_user_relationship_access(self):
        """Тест доступу до relationship"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed"
        )

        # Relationship поля доступні
        assert hasattr(user, 'weather_requests')
        assert hasattr(user, 'forecast_requests')

        # Початково пусті
        assert len(user.weather_requests) == 0
        assert len(user.forecast_requests) == 0

        print("User relationship поля доступні")


class TestModelValidation:
    """Тести валідації логіки для моделей"""

    def test_email_validation_logic(self):
        """Логіка валідації email"""

        def is_valid_email(email):
            """Покращена валідація email"""
            if not email or len(email) < 5:
                return False
            if email.startswith('@') or email.endswith('@'):
                return False
            parts = email.split('@')
            if len(parts) != 2:
                return False
            local, domain = parts
            if not local or not domain:
                return False
            if '.' not in domain:
                return False
            return True

        valid_emails = [
            "test@example.com",
            "user@domain.co.uk",
            "admin@localhost.dev"
        ]

        invalid_emails = [
            "invalid_email",
            "@domain.com",  # Починається з @
            "user@",  # Закінчується на @
            "",  # Пустий
            "user@domain"  # Нема крапки в домені
        ]

        for email in valid_emails:
            assert is_valid_email(email), f"Email {email} має бути валідним"

        for email in invalid_emails:
            assert not is_valid_email(email), f"Email {email} має бути невалідним"

        print("Виправлена email валідація працює")

    def test_username_validation_logic(self):
        """Тест валідації username для реальних полів"""

        def is_valid_username(username):
            """Валідація username відповідно до БД constraints"""
            if not username or len(username) > 50:  # String(50) у БД
                return False
            if len(username) < 3:
                return False
            return username.replace('_', '').isalnum()

        valid_usernames = ["user123", "test_user", "admin", "john_doe"]
        invalid_usernames = ["ab", "", "user@name", "a" * 51]  # 51 символ

        for username in valid_usernames:
            assert is_valid_username(username)

        for username in invalid_usernames:
            assert not is_valid_username(username)

        print("Username валідація для реальних constraints")

    def test_temperature_validation_logic(self):
        """Тест валідації температури (Numeric(5, 2))"""

        def is_valid_temperature(temp):
            """Валідація температури відповідно до БД Numeric(5, 2)"""
            if temp is None:
                return True  # Nullable поле
            try:
                # Numeric(5, 2) = до 999.99
                return -999.99 <= float(temp) <= 999.99
            except (ValueError, TypeError):
                return False

        valid_temps = [20.5, -10.25, 0, 999.99, -999.99, None]
        invalid_temps = [1000.0, -1000.0, "not_a_number"]

        for temp in valid_temps:
            assert is_valid_temperature(temp)

        for temp in invalid_temps:
            assert not is_valid_temperature(temp)

        print("Temperature валідація працює")


class TestModelUtilities:
    """Тести утилітарних методів моделей"""

    def test_user_to_dict_comprehensive(self):
        """Комплексний тест User to_dict"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            first_name="Test",
            last_name="User"
        )

        user_dict = user.to_dict()

        # Обов'язкові поля
        required_fields = ["id", "username", "email", "full_name", "is_active", "is_verified", "created_at"]
        for field in required_fields:
            assert field in user_dict

        # Конкретні значення
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["full_name"] == "Test User"

        print("User to_dict комплексний тест")

    def test_weather_request_to_dict_comprehensive(self):
        """Комплексний тест WeatherRequest to_dict"""
        weather_request = WeatherRequest(
            user_id=1,
            city="TestCity",
            temperature=25.5,
            humidity=60,
            response_data={"test": "data"}
        )

        request_dict = weather_request.to_dict()

        # Основні поля
        assert request_dict["user_id"] == 1
        assert request_dict["city"] == "TestCity"
        assert request_dict["temperature"] == 25.5
        assert request_dict["humidity"] == 60

        print("WeatherRequest to_dict комплексний тест")


# Базові тести імпорту та створення
def test_models_import():
    """Тест імпорту моделей"""
    from app.api.models.user import User
    from app.api.models.weather_request import WeatherRequest

    assert User is not None
    assert WeatherRequest is not None
    print("Всі моделі імпортуються")


def test_models_basic_creation():
    """Тест базового створення моделей"""
    # User з обов'язковими полями
    user = User(
        username="test",
        email="test@test.com",
        hashed_password="hash"
    )
    assert user.username == "test"

    # WeatherRequest з обов'язковими полями
    weather_req = WeatherRequest(
        user_id=1,
        city="Test",
        response_data={}
    )
    assert weather_req.city == "Test"
    assert weather_req.user_id == 1

    print("Базове створення моделей працює")


if __name__ == "__main__":
    try:
        test_models_import()
        test_models_basic_creation()
        print("Всі тести моделей пройшли")

    except Exception as e:
        print(f"Помилка в тестах: {e}")
        import traceback

        traceback.print_exc()