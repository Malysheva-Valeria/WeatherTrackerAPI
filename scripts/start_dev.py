"""
Скрипт для запуску проекту в режимі розробки
"""
import subprocess
import sys
import os
from pathlib import Path


def check_virtual_env():
    """Перевірка активності віртуального середовища"""
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("Віртуальне середовище не активовано")
        print("Виконайте перед запуском:")
        print("   venv\\Scripts\\activate  для Windows")
        print("   source venv/bin/activate для Mac/Linux")
        return False
    return True


def check_env_file():
    """Перевірка наявності .env файлів"""
    env_path = Path(".env")
    if not env_path.exists():
        print("Файл .env не знайдений")
        print("Скопіюйте .env.example в .env:")
        print("   cp .env.example .env для Mac/Linux")
        print("   copy .env.example .env для Windows")
        return False
    return True


def install_dependencies():
    """Встановлення залежностей якщо потрібно"""
    try:
        import fastapi
        print("FastAPI вже встановлений")
        return True
    except ImportError:
        print("Встановлення залежностей...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                           check=True)
            print("Залежності встановлено")
            return True
        except subprocess.CalledProcessError:
            print("Помилка встановлення залежностей")
            return False


def start_server():
    """Запуск серверу розробки"""
    print("Запуск сервера розробки")
    print("Документація доступна тут: http://127.0.0.1:8000/docs")
    print("Для зупинки Ctrl+C")
    print("-" * 50)

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "127.0.0.1",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("Сервер зупинено")
    except Exception as e:
        print(f"Помилка запуску: {e}")


def main():
    """Основна функція"""
    print("🌤️ WeatherTracker API - Запуск розробки")
    print("=" * 40)

    # Перевірки
    if not check_virtual_env():
        return

    if not check_env_file():
        return

    if not install_dependencies():
        return

    # Запуск
    start_server()


if __name__ == "__main__":
    main()