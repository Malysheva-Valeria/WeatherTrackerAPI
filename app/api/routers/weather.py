"""
Weather Router для WeatherTracker API

Ендпойнти для роботи з погодою та історією запитів
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
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

router = APIRouter(prefix="/weather", tags=["Weather"])


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