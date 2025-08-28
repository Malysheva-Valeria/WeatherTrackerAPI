"""
Analytics Service для WeatherTracker API
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_
from collections import Counter
import json
import csv
import io
from fastapi import Depends

from app.api.models.user import User
from app.api.models.weather_request import WeatherRequest
from app.database import get_db


class AnalyticsService:
    """Сервіс для аналітики та статистики"""

    def __init__(self, db: Session):
        self.db = db

    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Отримання персональної статистики користувача"""
        try:
            # Основна статистика запитів
            total_weather_requests = self.db.query(WeatherRequest).filter(
                WeatherRequest.user_id == user_id
            ).count()

            # Улюблені міста
            city_stats = self.db.query(
                WeatherRequest.city,
                func.count(WeatherRequest.id).label('count'),
                func.avg(WeatherRequest.temperature).label('avg_temp'),
                func.min(WeatherRequest.temperature).label('min_temp'),
                func.max(WeatherRequest.temperature).label('max_temp')
            ).filter(
                WeatherRequest.user_id == user_id,
                WeatherRequest.temperature.isnot(None)
            ).group_by(WeatherRequest.city).order_by(desc('count')).limit(10).all()

            favorite_cities = []
            for stat in city_stats:
                favorite_cities.append({
                    'city': stat.city,
                    'requests': stat.count,
                    'avg_temperature': round(stat.avg_temp, 1) if stat.avg_temp else None,
                    'min_temperature': round(stat.min_temp, 1) if stat.min_temp else None,
                    'max_temperature': round(stat.max_temp, 1) if stat.max_temp else None
                })

            # Часова активність (останні 30 днів)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_requests = self.db.query(WeatherRequest).filter(
                WeatherRequest.user_id == user_id,
                WeatherRequest.request_time >= thirty_days_ago
            ).all()

            # Аналіз по годинах
            hour_activity = Counter([req.request_time.hour for req in recent_requests])
            most_active_hour = hour_activity.most_common(1)[0][0] if hour_activity else None

            # Останній запит
            last_request = self.db.query(WeatherRequest).filter(
                WeatherRequest.user_id == user_id
            ).order_by(desc(WeatherRequest.request_time)).first()

            return {
                'user_id': user_id,
                'total_requests': total_weather_requests,
                'weather_requests': total_weather_requests,
                'forecast_requests': 0,
                'favorite_cities': favorite_cities,
                'activity_patterns': {
                    'most_active_hour': most_active_hour,
                    'requests_last_30_days': len(recent_requests),
                },
                'last_request': {
                    'city': last_request.city if last_request else None,
                    'time': last_request.request_time.isoformat() if last_request else None,
                    'temperature': last_request.temperature if last_request else None
                } if last_request else None,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Помилка отримання статистики користувача: {e}")
            return {
                'user_id': user_id,
                'total_requests': 0,
                'weather_requests': 0,
                'forecast_requests': 0,
                'favorite_cities': [],
                'activity_patterns': {'most_active_hour': None, 'requests_last_30_days': 0},
                'error': 'Не вдалося отримати статистику',
                'generated_at': datetime.utcnow().isoformat()
            }

    async def get_popular_cities(self, limit: int = 20) -> Dict[str, Any]:
        """Отримання топ популярних міст в системі"""
        try:
            # Статистика по містах
            city_stats = self.db.query(
                WeatherRequest.city,
                WeatherRequest.country,
                func.count(WeatherRequest.id).label('total_requests'),
                func.count(func.distinct(WeatherRequest.user_id)).label('unique_users'),
                func.avg(WeatherRequest.temperature).label('avg_temperature'),
                func.min(WeatherRequest.request_time).label('first_request'),
                func.max(WeatherRequest.request_time).label('last_request')
            ).filter(
                WeatherRequest.temperature.isnot(None)
            ).group_by(
                WeatherRequest.city,
                WeatherRequest.country
            ).order_by(desc('total_requests')).limit(limit).all()

            popular_cities = []
            for i, stat in enumerate(city_stats, 1):
                popular_cities.append({
                    'rank': i,
                    'city': stat.city,
                    'country': stat.country,
                    'total_requests': stat.total_requests,
                    'unique_users': stat.unique_users,
                    'avg_temperature': round(stat.avg_temperature, 1) if stat.avg_temperature else None,
                    'first_request': stat.first_request.isoformat() if stat.first_request else None,
                    'last_request': stat.last_request.isoformat() if stat.last_request else None,
                })

            # Загальна статистика
            total_cities = self.db.query(func.count(func.distinct(WeatherRequest.city))).scalar() or 0
            total_countries = self.db.query(func.count(func.distinct(WeatherRequest.country))).scalar() or 0

            return {
                'popular_cities': popular_cities,
                'summary': {
                    'total_cities_in_system': total_cities,
                    'total_countries_in_system': total_countries,
                    'showing_top': len(popular_cities),
                    'period_analyzed': 'all_time'
                },
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Помилка отримання популярних міст: {e}")
            return {
                'popular_cities': [],
                'summary': {'total_cities_in_system': 0, 'total_countries_in_system': 0, 'showing_top': 0},
                'error': 'Не вдалося отримати рейтинг міст',
                'generated_at': datetime.utcnow().isoformat()
            }

    async def get_temperature_trends(self, city: Optional[str] = None, period_days: int = 30) -> Dict[str, Any]:
        """Аналіз температурних трендів"""
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Базовий запит
            query = self.db.query(WeatherRequest).filter(
                WeatherRequest.request_time >= start_date,
                WeatherRequest.temperature.isnot(None)
            )

            if city:
                query = query.filter(WeatherRequest.city == city)

            requests = query.order_by(WeatherRequest.request_time).all()

            if not requests:
                return {
                    'city': city or 'No data',
                    'period_days': period_days,
                    'trends': [],
                    'summary': {'avg_temperature': 0, 'min_temperature': 0, 'max_temperature': 0,
                                'temperature_change': 0, 'data_points': 0}
                }

            # Аналіз температур
            temperatures = [req.temperature for req in requests]
            min_temp = min(temperatures)
            max_temp = max(temperatures)
            avg_temp = sum(temperatures) / len(temperatures)

            # Найпопулярніше місто в аналізі
            city_counts = {}
            for req in requests:
                if req.city:
                    city_counts[req.city] = city_counts.get(req.city, 0) + 1

            most_popular_city = max(city_counts.keys(), key=city_counts.get) if city_counts else (city or "No data")

            return {
                'city': most_popular_city,
                'period_days': period_days,
                'trends': [],
                'summary': {
                    'avg_temperature': round(avg_temp, 1),
                    'min_temperature': round(min_temp, 1),
                    'max_temperature': round(max_temp, 1),
                    'temperature_change': 0,
                    'data_points': len(temperatures)
                }
            }

        except Exception as e:
            print(f"Помилка аналізу температурних трендів: {e}")
            return {
                'city': city or 'No data',
                'period_days': period_days,
                'trends': [],
                'summary': {'avg_temperature': 0, 'min_temperature': 0, 'max_temperature': 0, 'temperature_change': 0,
                            'data_points': 0},
                'error': 'Не вдалося проаналізувати температурні тренди'
            }

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Швидкий огляд аналітики"""
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            # Загальна статистика
            total_requests = self.db.query(WeatherRequest).count()
            requests_30d = self.db.query(WeatherRequest).filter(
                WeatherRequest.request_time >= thirty_days_ago
            ).count()

            # Найпопулярніше місто
            popular_city_query = self.db.query(
                WeatherRequest.city,
                func.count(WeatherRequest.city).label('count')
            ).group_by(WeatherRequest.city).order_by(desc('count')).first()

            favorite_city = popular_city_query.city if popular_city_query else "Немає даних"

            # Середня температура
            avg_temp_query = self.db.query(
                func.avg(WeatherRequest.temperature)
            ).filter(
                and_(
                    WeatherRequest.request_time >= thirty_days_ago,
                    WeatherRequest.temperature.isnot(None)
                )
            ).scalar()

            avg_temperature = round(avg_temp_query, 1) if avg_temp_query else 0

            # Активні користувачі
            active_users = self.db.query(
                func.count(func.distinct(WeatherRequest.user_id))
            ).filter(WeatherRequest.request_time >= thirty_days_ago).scalar() or 0

            return {
                "total_requests": total_requests,
                "requests_last_30_days": requests_30d,
                "favorite_city": favorite_city,
                "avg_temperature_30d": avg_temperature,
                "active_users_30d": active_users,
                "summary_generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Помилка отримання огляду: {e}")
            return {
                "total_requests": 0,
                "requests_last_30_days": 0,
                "favorite_city": "Помилка",
                "avg_temperature_30d": 0,
                "active_users_30d": 0,
                "summary_generated_at": datetime.utcnow().isoformat()
            }

    async def export_to_csv(self, period_days: int = 30) -> str:
        """Експорт даних у CSV"""
        try:
            from_date = datetime.utcnow() - timedelta(days=period_days)

            requests = self.db.query(WeatherRequest).filter(
                WeatherRequest.request_time >= from_date
            ).order_by(WeatherRequest.request_time).all()

            output = io.StringIO()
            writer = csv.writer(output)

            # Заголовки
            writer.writerow([
                'ID', 'User ID', 'City', 'Country', 'Temperature', 'Description', 'Request Time', 'Is Mock'
            ])

            # Дані
            for req in requests:
                writer.writerow([
                    req.id or '',
                    req.user_id or '',
                    req.city or '',
                    req.country or '',
                    req.temperature if req.temperature is not None else '',
                    req.description or '',
                    req.request_time.isoformat() if req.request_time else '',
                    getattr(req, 'is_mock', False) or False
                ])

            csv_content = output.getvalue()
            output.close()
            return csv_content

        except Exception as e:
            print(f"Деталі помилки CSV: {e}")
            raise Exception(f"Помилка експорту в CSV: {str(e)}")

    async def export_to_json(self, period_days: int = 30) -> List[Dict[str, Any]]:
        """Експорт даних у JSON"""
        try:
            from_date = datetime.utcnow() - timedelta(days=period_days)

            requests = self.db.query(WeatherRequest).filter(
                WeatherRequest.request_time >= from_date
            ).order_by(WeatherRequest.request_time).all()

            result = []
            for req in requests:
                result.append({
                    "id": req.id,
                    "user_id": req.user_id,
                    "city": req.city,
                    "country": req.country,
                    "temperature": req.temperature,
                    "description": req.description,
                    "request_time": req.request_time.isoformat() if req.request_time else None,
                    "is_mock": getattr(req, 'is_mock', False)
                })

            return result

        except Exception as e:
            print(f"Деталі помилки JSON: {e}")
            raise Exception(f"Помилка експорту в JSON: {str(e)}")

async def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Отримання інстанс Analytics Service"""
    return AnalyticsService(db)