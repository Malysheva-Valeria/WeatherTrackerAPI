"""
Weather Router для WeatherTracker API

Ендпойнти для роботи з погодою та історією запитів
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies import get_db, get_current_active_user
from app.api.services.weather_service import get_weather_service
from app.api.models.user import User
from app.api.models.weather_request import WeatherRequest
from app.api.schemas.weather import (
    WeatherRequest as WeatherRequestSchema,
    CurrentWeatherResponse,
    WeatherHistoryItem,
    WeatherHistoryResponse
)
from app.api.schemas.base import MessageResponse
from app.api.schemas.forecast import ForecastResponse

import logging
from datetime import datetime


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/weather", tags=["Weather"])

WeatherResponse = CurrentWeatherResponse

async def save_weather_request(
        db: Session,
        user_id: int,
        city: str,
        country: str,
        weather_data: dict,
        is_cached: bool = False,
        is_mock: bool = False
) -> None:
    """Збереження погодного запиту в історію"""
    try:
        from app.api.models.weather_request import WeatherRequest as WeatherRequestModel

        weather_request = WeatherRequestModel(
            user_id=user_id,
            city=city,
            country=country,
            temperature=weather_data.get('temperature'),
            feels_like=weather_data.get('feels_like'),
            description=weather_data.get('description', ''),
            weather_condition=weather_data.get('condition', ''),
            humidity=weather_data.get('humidity'),
            pressure=weather_data.get('pressure'),
            wind_speed=weather_data.get('wind_speed'),
            wind_direction=weather_data.get('wind_direction'),
            request_time=datetime.utcnow(),
            response_data=weather_data,
            is_cached=is_cached,
            is_mock=is_mock
        )

        db.add(weather_request)
        db.commit()
        logger.info(f"Weather request saved for user {user_id}, city {city}")

    except Exception as e:
        logger.error(f"Error saving weather request: {e}")
        db.rollback()

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

        # Збереження запиту в історію
        weather_request = WeatherRequest(
            user_id=current_user.id,
            city=formatted_data["city"],
            country=formatted_data["country"],
            temperature=formatted_data["temperature"],
            feels_like=formatted_data["feels_like"],
            description=formatted_data["description"],
            weather_condition=formatted_data["condition"],
            humidity=formatted_data["humidity"],
            pressure=formatted_data["pressure"],
            wind_speed=formatted_data["wind_speed"],
            wind_direction=formatted_data["wind_direction"],
            is_cached=formatted_data["cached"],
            is_mock=formatted_data["mock"],
            response_data=raw_weather_data
        )

        db.add(weather_request)
        db.commit()
        db.refresh(weather_request)

        return CurrentWeatherResponse(**formatted_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка отримання даних погоди: {str(e)}"
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
    # Базовий запит
    query = db.query(WeatherRequest).filter(
        WeatherRequest.user_id == current_user.id
    )

    # Фільтр за містом якщо вказано
    if city:
        query = query.filter(WeatherRequest.city.ilike(f"%{city}%"))

    # Сортування за часом (найновіші першими)
    query = query.order_by(WeatherRequest.request_time.desc())

    # Загальна кількість
    total = query.count()

    # Пагінація
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    # Конвертація в схеми
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
    # Пошук запису
    weather_request = db.query(WeatherRequest).filter(
        WeatherRequest.id == request_id,
        WeatherRequest.user_id == current_user.id
    ).first()

    if not weather_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис історії не знайдений"
        )

    # Видалення
    db.delete(weather_request)
    db.commit()

    return MessageResponse(message=f"Запис історії для міста '{weather_request.city}' видалено")


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
    # Підрахунок кількості записів
    count = db.query(WeatherRequest).filter(
        WeatherRequest.user_id == current_user.id
    ).count()

    # Видалення всіх записів користувача
    db.query(WeatherRequest).filter(
        WeatherRequest.user_id == current_user.id
    ).delete()
    db.commit()

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
    from sqlalchemy import func, distinct

    # Загальна кількість запитів
    total_requests = db.query(WeatherRequest).filter(
        WeatherRequest.user_id == current_user.id
    ).count()

    # Кількість унікальних міст
    unique_cities = db.query(distinct(WeatherRequest.city)).filter(
        WeatherRequest.user_id == current_user.id
    ).count()

    # Найпопулярніше місто
    popular_city = db.query(
        WeatherRequest.city,
        func.count(WeatherRequest.id).label('count')
    ).filter(
        WeatherRequest.user_id == current_user.id
    ).group_by(WeatherRequest.city).order_by(
        func.count(WeatherRequest.id).desc()
    ).first()

    # Останній запит
    last_request = db.query(WeatherRequest).filter(
        WeatherRequest.user_id == current_user.id
    ).order_by(WeatherRequest.request_time.desc()).first()

    return {
        "total_requests": total_requests,
        "unique_cities": unique_cities,
        "most_popular_city": {
            "city": popular_city.city if popular_city else None,
            "requests_count": popular_city.count if popular_city else 0
        },
        "last_request": {
            "city": last_request.city if last_request else None,
            "time": last_request.request_time.isoformat() if last_request else None
        }
    }

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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка отримання прогнозу погоди: {str(e)}"
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

        logger.info(
            f"Прогноз по координатах отримано успішно: {forecast_data.city if hasattr(forecast_data, 'city') else 'координати'}")
        return forecast_data

    except ValueError as e:
        logger.warning(f"Помилка валідації координат: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Помилка координат: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Помилка отримання прогнозу по координатах: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Помилка отримання прогнозу по координатах: {str(e)}"
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

        # Збереження в історію
        await save_weather_request(
            db=db,
            user_id=current_user.id,
            city=weather_data.get("city", f"Координати {latitude}, {longitude}"),
            country=weather_data.get("country", "Unknown"),
            weather_data=weather_data,
            is_cached=weather_data.get("cached", False),
            is_mock=weather_data.get("mock", False)
        )
        logger.info(f"Поточна погода по координатах отримана: {weather_data.get('city', 'координати')}")
        return weather_data

    except ValueError as e:
        logger.warning(f"Помилка валідації координат: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Помилка координат: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Помилка отримання поточної погоди по координатах: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Помилка отримання поточної погоди: {str(e)}"
        )