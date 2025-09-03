"""
Unit тести для dependencies з мокуванням
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_current_user
from app.api.models.user import User


class TestDependencies:
    """Unit тести для dependencies з мокуванням"""

    @pytest.fixture
    def mock_db(self):
        """Мок бази даних"""
        return Mock()

    @pytest.fixture
    def mock_user(self):
        """Мок користувача"""
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.is_active = True
        user.is_verified = True
        return user

    @pytest.fixture
    def mock_credentials(self):
        """Мок credentials"""
        credentials = Mock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "valid_jwt_token"
        return credentials

    @patch('app.dependencies.get_auth_service')
    def test_get_current_user_success(self, mock_get_auth_service, mock_db, mock_user):
        """Тест успішного отримання поточного користувача"""
        # Arrange
        mock_auth_service = Mock()
        mock_auth_service.get_user_by_token.return_value = mock_user
        mock_get_auth_service.return_value = mock_auth_service

        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        # Act
        result = get_current_user(mock_credentials, mock_db)

        # Assert
        assert result == mock_user
        mock_get_auth_service.assert_called_once()
        mock_auth_service.get_user_by_token.assert_called_once_with(mock_db, "valid_token")

        print("get_current_user success test пройшов")

    @patch('app.dependencies.get_auth_service')
    def test_get_current_user_invalid_token(self, mock_get_auth_service, mock_db):
        """Тест з невалідним токеном"""
        # Arrange
        mock_auth_service = Mock()
        mock_auth_service.get_user_by_token.return_value = None  # Невалідний токен
        mock_get_auth_service.return_value = mock_auth_service

        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Невалідний токен аутентифікації" in exc_info.value.detail

        print("get_current_user invalid token test пройшов")

    @patch('app.dependencies.get_auth_service')
    def test_get_current_user_inactive_user(self, mock_get_auth_service, mock_db, mock_user):
        """Тест з неактивним користувачем через get_current_active_user"""
        # Arrange
        mock_user.is_active = False  # Неактивний користувач
        mock_auth_service = Mock()
        mock_auth_service.get_user_by_token.return_value = mock_user
        mock_get_auth_service.return_value = mock_auth_service

        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        # Act - спочатку отримання користувача
        result = get_current_user(mock_credentials, mock_db)

        # Assert - користувач отримується, але він неактивний
        assert result == mock_user
        assert result.is_active == False

        # Тепер тестування get_current_active_user окремо
        from app.dependencies import get_current_active_user
        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(mock_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Користувач неактивний" in exc_info.value.detail

        print("get_current_user inactive user test пройшов")

    @patch('app.dependencies.get_auth_service')
    def test_get_current_user_service_exception(self, mock_get_auth_service, mock_db):
        """Тест коли AuthService кидає виняток"""
        # Arrange
        mock_auth_service = Mock()
        mock_auth_service.get_user_by_token.side_effect = Exception("Auth service error")
        mock_get_auth_service.return_value = mock_auth_service

        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "some_token"

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert "Auth service error" in str(exc_info.value)

        print("get_current_user service exception test пройшов")

    def test_get_current_active_user_success(self, mock_user):
        """Тест успішного отримання активного користувача"""
        from app.dependencies import get_current_active_user

        # Arrange
        mock_user.is_active = True

        # Act
        result = get_current_active_user(mock_user)

        # Assert
        assert result == mock_user

        print("get_current_active_user success test пройшов")

    def test_get_current_verified_user_success(self, mock_user):
        """Тест успішного отримання верифікованого користувача"""
        from app.dependencies import get_current_verified_user

        # Arrange
        mock_user.is_active = True
        mock_user.is_verified = True

        # Act
        result = get_current_verified_user(mock_user)

        # Assert
        assert result == mock_user

        print("get_current_verified_user success test пройшов")

    def test_get_current_verified_user_not_verified(self, mock_user):
        """Тест з неверифікованим користувачем"""
        from app.dependencies import get_current_verified_user

        # Arrange
        mock_user.is_active = True
        mock_user.is_verified = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_current_verified_user(mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "не верифікований" in exc_info.value.detail

        print("get_current_verified_user not verified test пройшов")

    @patch('app.dependencies.get_auth_service')
    def test_get_current_user_optional_with_valid_token(self, mock_get_auth_service, mock_db, mock_user):
        """Тест опціональної аутентифікації з валідним токеном"""
        from app.dependencies import get_current_user_optional

        # Arrange
        mock_auth_service = Mock()
        mock_auth_service.get_user_by_token.return_value = mock_user
        mock_get_auth_service.return_value = mock_auth_service

        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"

        # Act
        result = get_current_user_optional(mock_db, mock_credentials)

        # Assert
        assert result == mock_user

        print("get_current_user_optional with valid token test пройшов")

    def test_get_current_user_optional_without_credentials(self, mock_db):
        """Тест опціональної аутентифікації без credentials"""
        from app.dependencies import get_current_user_optional

        # Act
        result = get_current_user_optional(mock_db, None)

        # Assert
        assert result is None

        print("get_current_user_optional without credentials test пройшов")


def test_dependencies_import():
    """Тест імпортів dependencies"""
    from app.dependencies import (
        get_current_user,
        get_current_active_user,
        get_current_verified_user,
        get_current_superuser,
        get_current_user_optional,
        get_db,
        get_auth_service
    )

    assert callable(get_current_user)
    assert callable(get_current_active_user)
    assert callable(get_current_verified_user)
    assert callable(get_current_superuser)
    assert callable(get_current_user_optional)
    assert callable(get_db)
    assert callable(get_auth_service)

    print("Всі dependencies функції імпортуються")


def test_auth_service_function():
    """Тест функції get_auth_service"""
    from app.dependencies import get_auth_service

    # Отримання auth service
    auth_service = get_auth_service()

    # Перевірка що це справді AuthService
    assert auth_service is not None
    assert hasattr(auth_service, 'get_user_by_token')
    assert callable(auth_service.get_user_by_token)

    print("get_auth_service функція працює та повертає AuthService")


if __name__ == "__main__":
    try:
        test_dependencies_import()
        test_auth_service_function()
        print("Dependency тести пройшли")

    except Exception as e:
        print(f"Помилка в dependency тестах: {e}")
        import traceback

        traceback.print_exc()