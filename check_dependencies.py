"""
Скрипт для перевірки встановлення всіх необхідних залежностей
та налаштувань для проекту
"""
import sys
import subprocess
import importlib
import os
from pathlib import Path


def check_python_version():
    """Перевірка версії Python"""
    print("Перевірка версії Python")
    version = sys.version_info

    if version.major == 3 and version.minor >= 11:
        print(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"Python {version.major}.{version.minor}.{version.micro} - потрібна версія 3.11+")
        return False


def check_git():
    """Перевірка наявності Git"""
    print("Перевірка Git")
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        print(f"Є {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("Git не встановлений")
        return False


def check_virtual_environment():
    """Перевірка чи активовано віртуальне середовище"""
    print("Перевірка віртуального середовища...")

    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Віртуальне середовище активовано")
        return True
    else:
        print("Віртуальне середовище не активовано")
        print("Виконайте: venv\\Scripts\\activate (Windows) або source venv/bin/activate (Mac/Linux)")
        return False


def check_dependencies():
    """Перевірка встановлення основних залежностей"""
    print("Перевірка залежностей...")

    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'sqlalchemy': 'SQLAlchemy',
        'alembic': 'Alembic',
        'pydantic': 'Pydantic',
        'httpx': 'HTTPX',
        'passlib': 'Passlib',
        'python_jose': 'Python JOSE',
        'psycopg2': 'Psycopg2',
        'pytest': 'Pytest',
        'python_dotenv': 'Python Dotenv'
    }

    installed = []
    missing = []

    for package, name in required_packages.items():
        try:
            importlib.import_module(package)
            print(f"{name} - є ")
            installed.append(package)
        except ImportError:
            print(f"{name} - не встановлений")
            missing.append(package)

    return len(missing) == 0, missing


def check_env_setup():
    """Перевірка налаштування середовища"""
    print("Перевірка налаштувань середовища...")

    # Перевірка .env файлу
    if os.path.exists('.env'):
        print(".env файл існує")
        env_ok = True
    else:
        print(".env файл не знайдений")
        print("Скопіюйте .env.example в .env та налаштуйте змінні")
        env_ok = False

    return env_ok


def test_fastapi_import():
    """Тестування імпорту FastAPI додатку"""
    print("Тестування FastAPI додатку...")

    try:
        from app.main import app
        from app.config import settings
        print("FastAPI додаток успішно імпортовано")
        print(f"Конфігурація завантажена: DEBUG={settings.DEBUG}")
        return True
    except ImportError as e:
        print(f"Помилка імпорту FastAPI додатку: {e}")
        return False
    except Exception as e:
        print(f"Помилка в коді додатку: {e}")
        return False


def main():
    """Основна функція перевірки"""
    print("WeatherTracker API - Перевірка середовища")
    print("=" * 50)

    checks = []

    # Виконання всіх перевірок
    checks.append(("Python версія", check_python_version()))
    checks.append(("Git", check_git()))
    checks.append(("Віртуальне середовище", check_virtual_environment()))
    checks.append(("Залежності", check_dependencies()[0]))
    checks.append(("Налаштування середовища", check_env_setup()))
    checks.append(("FastAPI додаток", test_fastapi_import()))

if __name__ == "__main__":
    main()