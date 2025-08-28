"""
Analytics Router для WeatherTracker API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
import csv
import io

from app.database import get_db
from app.dependencies import get_current_user
from app.api.models.user import User
from app.api.services.analytics_service import get_analytics_service, AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=Dict[str, Any])
async def get_analytics_summary(
        current_user: User = Depends(get_current_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Швидкий огляд аналітики системи
    """
    try:
        summary = await analytics_service.get_analytics_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка отримання огляду: {str(e)}")


@router.get("/user/stats", response_model=Dict[str, Any])
async def get_user_statistics(
        current_user: User = Depends(get_current_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Персональна статистика користувача

    Повертає:
    - Кількість запитів погоди та прогнозів
    - Улюблені міста з температурною статистикою
    - Найпопулярніші погодні умови
    - Патерни активності (години, дні тижня)
    - Інформацію про останній запит
    """
    try:
        stats = await analytics_service.get_user_statistics(current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка отримання статистики: {str(e)}")


@router.get("/cities/popular", response_model=Dict[str, Any])
async def get_popular_cities(
        limit: int = Query(default=10, ge=1, le=50, description="Кількість міст для показу"),
        current_user: User = Depends(get_current_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Топ популярних міст в системі

    Повертає рейтинг міст за:
    - Загальною кількістю запитів
    - Кількістю унікальних користувачів
    - Середньою температурою
    - Динамікою росту запитів
    """
    try:
        popular_cities = await analytics_service.get_popular_cities(limit=limit)
        return popular_cities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка отримання популярних міст: {str(e)}")


@router.get("/temperature/trends", response_model=Dict[str, Any])
async def get_temperature_trends(
        city: Optional[str] = Query(default=None, description="Конкретне місто для аналізу"),
        period_days: int = Query(default=30, ge=1, le=365, description="Період аналізу в днях"),
        current_user: User = Depends(get_current_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Аналіз температурних трендів

    Аналізує температурні дані за вказаний період та повертає:
    - Статистику температур (мін, макс, середня)
    - Тренд зміни температури
    - Денні середні значення
    - Загальну кількість точок даних
    """
    try:
        trends = await analytics_service.get_temperature_trends(
            city=city,
            period_days=period_days
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка аналізу температурних трендів: {str(e)}")


@router.get("/export/csv")
async def export_weather_data_csv(
        period_days: int = Query(default=30, ge=1, le=365, description="Період для експорту"),
        current_user: User = Depends(get_current_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Експорт погодних даних у CSV форматі
    """
    try:
        csv_data = await analytics_service.export_to_csv(period_days=period_days)

        # Створення відповідей з правильними заголовками для CSV
        response = Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=weather_data_{period_days}d.csv"
            }
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка експорту в CSV: {str(e)}")


@router.get("/export/json")
async def export_weather_data_json(
        period_days: int = Query(default=30, ge=1, le=365, description="Період для експорту"),
        current_user: User = Depends(get_current_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Експорт погодних даних у JSON форматі
    """
    try:
        json_data = await analytics_service.export_to_json(period_days=period_days)

        from datetime import datetime

        return {
            "data": json_data,
            "total_records": len(json_data),
            "period_days": period_days,
            "exported_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка експорту в JSON: {str(e)}")


# Додатковий endpoint для адміністрування
@router.get("/admin/system-overview")
async def get_system_overview(
        current_user: User = Depends(get_current_user),
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Розширений огляд системи (тільки для адміністраторів)
    """
    # Перевірка на is_superuser
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Недостатньо прав для доступу")

    try:
        from app.api.models.weather_request import WeatherRequest

        # Статистика по всій системі
        total_users = analytics_service.db.query(func.count(User.id)).scalar()
        total_requests = analytics_service.db.query(func.count(WeatherRequest.id)).scalar()

        # Активність за сьогодні
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())

        today_requests = analytics_service.db.query(WeatherRequest).filter(
            WeatherRequest.created_at >= today_start
        ).count()

        # Топ користувачі
        top_users = analytics_service.db.query(
            User.username,
            func.count(WeatherRequest.id).label('request_count')
        ).join(WeatherRequest, User.id == WeatherRequest.user_id).group_by(
            User.id, User.username
        ).order_by(func.count(WeatherRequest.id).desc()).limit(5).all()

        return {
            "system_stats": {
                "total_users": total_users,
                "total_requests": total_requests,
                "requests_today": today_requests
            },
            "top_users": [
                {"username": username, "requests": count}
                for username, count in top_users
            ],
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка отримання огляду системи: {str(e)}")