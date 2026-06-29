"""
Weather Router для WeatherTracker API

Ендпойнти для роботи з погодою та історією запитів
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.models.user import User
from app.api.repositories.weather_repository import WeatherRequestRepository
from app.api.schemas.base import MessageResponse
from app.api.schemas.forecast import ForecastResponse
from app.api.schemas.weather import CurrentWeatherResponse, WeatherHistoryItem, WeatherHistoryResponse
from app.api.services.weather_service import get_weather_service
from app.dependencies import get_current_active_user, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/weather", tags=["Weather"])

WeatherResponse = CurrentWeatherResponse


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
        city: str = Query(..., description="Назва міста для прогнозу погоди"),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Отримання поточної погоди для міста

    Args:
        city: Назва міста
        current_user: Поточний активний користувач
        db: Сесія бази даних

    Returns:
        CurrentWeatherResponse: Дані про поточну погоду
    """
    try:
        # Отримання даних погоди через сервіс
        weather_service = get_weather_service()
        raw_weather_data = await weather_service.get_current_weather(city)
        formatted_data = weather_service.format_weather_response(raw_weather_data)

        # Збереження запиту в історію через репозиторій
        WeatherRequestRepository(db).create_from_weather_data(
            user_id=current_user.id,
            city=formatted_data["city"],
            country=formatted_data["country"],
            weather_data=formatted_data,
            raw_data=raw_weather_data,
            is_cached=formatted_data["cached"],
            is_mock=formatted_data["mock"],
        )

        return CurrentWeatherResponse(**formatted_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception:
        logger.exception("Помилка отримання даних погоди для міста %s", city)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка під час отримання даних погоди"
        )


@router.get("/history", response_model=WeatherHistoryResponse)
async def get_weather_history(
        page: int = Query(1, ge=1, description="Номер сторінки"),
        size: int = Query(10, ge=1, le=100, description="Кількість записів на сторінці"),
        city: str = Query(None, description="Фільтр за містом"),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Отримання історії погодних запитів користувача

    Args:
        page: Номер сторінки
        size: Кількість записів на сторінці
        city: Опціональний фільтр за містом
        current_user: Поточний активний користувач
        db: Сесія бази даних

    Returns:
        WeatherHistoryResponse: Список історії запитів
    """
    items, total = WeatherRequestRepository(db).list_for_user(
        current_user.id, page=page, size=size, city=city
    )

    history_items = [WeatherHistoryItem.from_orm(item) for item in items]

    return WeatherHistoryResponse(
        items=history_items,
        total=total,
        page=page,
        size=size
    )


@router.delete("/history/{request_id}", response_model=MessageResponse)
async def delete_weather_history_item(
        request_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Видалення запису з історії погодних запитів

    Args:
        request_id: ID запису для видалення
        current_user: Поточний активний користувач
        db: Сесія бази даних

    Returns:
        MessageResponse: Повідомлення про успішне видалення
    """
    repo = WeatherRequestRepository(db)
    weather_request = repo.get_for_user(current_user.id, request_id)

    if not weather_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис історії не знайдений"
        )

    city_name = weather_request.city
    repo.delete(weather_request)

    return MessageResponse(message=f"Запис історії для міста '{city_name}' видалено")


@router.delete("/history", response_model=MessageResponse)
async def clear_weather_history(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Очистка всієї історії погодних запитів користувача

    Args:
        current_user: Поточний активний користувач
        db: Сесія бази даних

    Returns:
        MessageResponse: Повідомлення про успішне очищення
    """
    count = WeatherRequestRepository(db).delete_all_for_user(current_user.id)

    return MessageResponse(message=f"Видалено {count} записів з історії погоди")


@router.get("/stats")
async def get_weather_stats(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Отримання статистики погодних запитів користувача

    Args:
        current_user: Поточний активний користувач
        db: Сесія бази даних

    Returns:
        dict: Статистика запитів
    """
    return WeatherRequestRepository(db).stats_for_user(current_user.id)

@router.get("/forecast", response_model=ForecastResponse)
async def get_weather_forecast(
        city: str = Query(None, description="Назва міста"),
        latitude: float = Query(None, ge=-90, le=90, description="Широта"),
        longitude: float = Query(None, ge=-180, le=180, description="Довгота"),
        days: int = Query(5, ge=1, le=7, description="Кількість днів прогнозу (1-7)"),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Отримання прогнозу погоди на кілька днів

    Можна вказати або місто, або координати:
    - **city**: Назва міста (наприклад: Kyiv, London, New York)
    - **latitude + longitude**: Координати локації
    - **days**: Кількість днів прогнозу від 1 до 7

    Прогноз включає:
    - Температуру (мін/макс/середня) для кожного дня
    - Погодні умови та детальний опис
    - Атмосферні показники (вологість, тиск, видимість)
    - Вітер та опади
    - Загальну статистику за весь період
    - Кешування результатів для швидкості
    """
    try:
        # Валідація параметрів
        if not city and (latitude is None or longitude is None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вкажіть або назву міста, або координати (latitude + longitude)"
            )

        # Отримання прогнозу через weather service
        weather_service = get_weather_service()
        forecast = await weather_service.get_5day_forecast(
            city=city,
            latitude=latitude,
            longitude=longitude,
            days=days,
            user_id=current_user.id,
            db=db
        )

        return forecast

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception:
        logger.exception("Помилка отримання прогнозу погоди (city=%s)", city)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутрішня помилка під час отримання прогнозу погоди"
        )

@router.get("/forecast/coordinates", response_model=ForecastResponse, tags=["Weather"])
async def get_forecast_by_coordinates(
        latitude: float = Query(..., ge=-90, le=90, description="Широта (-90 до 90)"),
        longitude: float = Query(..., ge=-180, le=180, description="Довгота (-180 до 180)"),
        days: int = Query(5, ge=1, le=7, description="Кількість днів прогнозу (1-7)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Отримання прогнозу погоди по координатах (широта/довгота)

    Цей endpoint дозволяє отримати точний прогноз для будь-якої точки на Землі
    без необхідності знати назву міста.

    **Параметри:**
    - **latitude**: Широта від -90 (Південний полюс) до 90 (Північний полюс)
    - **longitude**: Довгота від -180 до 180 градусів
    - **days**: Кількість днів прогнозу (від 1 до 7)

    **Приклади координат:**
    - Kyiv: lat=50.4501, lon=30.5234
    - London: lat=51.5074, lon=-0.1278
    - New York: lat=40.7128, lon=-74.0060
    - Sydney: lat=-33.8688, lon=151.2093
    """
    try:
        logger.info(
            f"Запит прогнозу по координатах: {latitude}, {longitude} на {days} днів для користувача {current_user.id}")

        # Отримання прогнозу від сервісу
        weather_service = get_weather_service()
        forecast_data = await weather_service.get_5day_forecast(
            city=None,  # Без міста
            latitude=latitude,
            longitude=longitude,
            days=days,
            user_id=current_user.id,
            db=db
        )

        resolved_city = forecast_data.city if hasattr(forecast_data, 'city') else 'координати'
        logger.info("Прогноз по координатах отримано успішно: %s", resolved_city)
        return forecast_data

    except ValueError as e:
        logger.warning(f"Помилка валідації координат: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Помилка координат: {str(e)}"
        )
    except Exception:
        logger.exception("Помилка отримання прогнозу по координатах %s, %s", latitude, longitude)
        raise HTTPException(
            status_code=500,
            detail="Внутрішня помилка під час отримання прогнозу по координатах"
        )


@router.get("/current/coordinates", response_model=WeatherResponse, tags=["Weather"])
async def get_current_weather_by_coordinates(
        latitude: float = Query(..., ge=-90, le=90, description="Широта (-90 до 90)"),
        longitude: float = Query(..., ge=-180, le=180, description="Довгота (-180 до 180)"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Отримання поточної погоди по координатах

    **Параметри:**
    - **latitude**: Широта від -90 до 90 градусів
    - **longitude**: Довгота від -180 до 180 градусів
    """
    try:
        logger.info(f"Запит поточної погоди по координатах: {latitude}, {longitude} для користувача {current_user.id}")

        # Отримання погоди від сервісу
        weather_service = get_weather_service()

        # Для координат використовуємо спеціальний метод
        raw_weather_data = await weather_service.get_current_weather_by_coordinates(
            latitude=latitude,
            longitude=longitude
        )

        # Форматування відповіді
        weather_data = weather_service.format_weather_response(raw_weather_data)

        # Збереження в історію через репозиторій
        WeatherRequestRepository(db).create_from_weather_data(
            user_id=current_user.id,
            city=weather_data.get("city", f"Координати {latitude}, {longitude}"),
            country=weather_data.get("country", "Unknown"),
            weather_data=weather_data,
            raw_data=raw_weather_data,
            is_cached=weather_data.get("cached", False),
            is_mock=weather_data.get("mock", False),
        )
        logger.info(f"Поточна погода по координатах отримана: {weather_data.get('city', 'координати')}")
        return weather_data

    except ValueError as e:
        logger.warning(f"Помилка валідації координат: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Помилка координат: {str(e)}"
        )
    except Exception:
        logger.exception("Помилка отримання поточної погоди по координатах %s, %s", latitude, longitude)
        raise HTTPException(
            status_code=500,
            detail="Внутрішня помилка під час отримання поточної погоди"
        )
