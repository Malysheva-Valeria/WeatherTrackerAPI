"""Unit тести для dependencies"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer

from app.dependencies import get_current_user
from app.api.models.user import User


class TestDependencies:
    """Unit тести для dependencies"""

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
        return user

    @patch('app.dependencies.AuthService')
    def test_get_current_user_success(self, mock_auth_service_class, mock_db, mock_user):
        """Тест успішного отримання поточного користувача"""
        # Налаштування мока AuthService
        mock_auth_service = Mock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.get_user_by_token.return_value = mock_user

        # Мок credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        # Виклик dependency
        result = get_current_user(mock_credentials, mock_db)

        # Перевірки
        assert result == mock_user
        mock_auth_service.get_user_by_token.assert_called_once_with(mock_db, "valid_token")

    @patch('app.dependencies.AuthService')
    def test_get_current_user_invalid_token(self, mock_auth_service_class, mock_db):
        """Тест з невалідним токеном"""
        # Налаштування мока AuthService для поверення None
        mock_auth_service = Mock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.get_user_by_token.return_value = None

        # Мок credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "invalid_token"

        # Очікування HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @patch('app.dependencies.AuthService')
    def test_get_current_user_inactive_user(self, mock_auth_service_class, mock_db, mock_user):
        """Тест з неактивним користувачем"""
        # Налаштування неактивного користувача
        mock_user.is_active = False

        mock_auth_service = Mock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.get_user_by_token.return_value = mock_user

        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        # Очікування HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Inactive user" in str(exc_info.value.detail)