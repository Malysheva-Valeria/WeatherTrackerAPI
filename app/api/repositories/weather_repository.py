"""
Репозиторій для роботи з історією погодних запитів (WeatherRequest).

Уся робота з БД, повʼязана з WeatherRequest, зосереджена тут, щоб роутери
лишались тонкими, а бізнес-логіка не зналася на деталях SQLAlchemy.
"""
import logging
from typing import List, Optional, Tuple

from sqlalchemy import distinct, func

from app.api.models.weather_request import WeatherRequest
from app.api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class WeatherRequestRepository(BaseRepository[WeatherRequest]):
    """Доступ до даних історії погодних запитів користувача."""

    model = WeatherRequest

    def create_from_weather_data(
        self,
        *,
        user_id: int,
        city: str,
        country: Optional[str],
        weather_data: dict,
        raw_data: Optional[dict] = None,
        is_cached: bool = False,
        is_mock: bool = False,
        commit: bool = True,
    ) -> Optional[WeatherRequest]:
        """Створює запис історії з форматованих даних погоди.

        Помилка збереження не повинна валити основний запит погоди — тому
        вона логується, робиться rollback, і повертається None.
        """
        weather_request = WeatherRequest(
            user_id=user_id,
            city=city,
            country=country,
            temperature=weather_data.get("temperature"),
            feels_like=weather_data.get("feels_like"),
            description=weather_data.get("description", ""),
            weather_condition=weather_data.get("condition", ""),
            humidity=weather_data.get("humidity"),
            pressure=weather_data.get("pressure"),
            wind_speed=weather_data.get("wind_speed"),
            wind_direction=weather_data.get("wind_direction"),
            response_data=raw_data if raw_data is not None else weather_data,
            is_cached=is_cached,
            is_mock=is_mock,
        )
        try:
            return self.add(weather_request, commit=commit)
        except Exception:
            logger.exception("Не вдалося зберегти погодний запит для user_id=%s", user_id)
            self.db.rollback()
            return None

    def list_for_user(
        self,
        user_id: int,
        *,
        page: int = 1,
        size: int = 10,
        city: Optional[str] = None,
    ) -> Tuple[List[WeatherRequest], int]:
        """Повертає сторінку історії користувача та загальну кількість записів."""
        query = self.db.query(WeatherRequest).filter(WeatherRequest.user_id == user_id)

        if city:
            query = query.filter(WeatherRequest.city.ilike(f"%{city}%"))

        total = query.count()
        items = (
            query.order_by(WeatherRequest.request_time.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return items, total

    def get_for_user(self, user_id: int, request_id: int) -> Optional[WeatherRequest]:
        """Запис історії, що належить саме цьому користувачу (інакше None)."""
        return (
            self.db.query(WeatherRequest)
            .filter(
                WeatherRequest.id == request_id,
                WeatherRequest.user_id == user_id,
            )
            .first()
        )

    def delete_all_for_user(self, user_id: int) -> int:
        """Видаляє всю історію користувача, повертає кількість видалених записів."""
        query = self.db.query(WeatherRequest).filter(WeatherRequest.user_id == user_id)
        count = query.count()
        query.delete(synchronize_session=False)
        self.db.commit()
        return count

    def stats_for_user(self, user_id: int) -> dict:
        """Зведена статистика запитів користувача."""
        base = self.db.query(WeatherRequest).filter(WeatherRequest.user_id == user_id)

        total_requests = base.count()
        unique_cities = (
            self.db.query(distinct(WeatherRequest.city))
            .filter(WeatherRequest.user_id == user_id)
            .count()
        )
        popular_city = (
            self.db.query(
                WeatherRequest.city,
                func.count(WeatherRequest.id).label("count"),
            )
            .filter(WeatherRequest.user_id == user_id)
            .group_by(WeatherRequest.city)
            .order_by(func.count(WeatherRequest.id).desc())
            .first()
        )
        last_request = base.order_by(WeatherRequest.request_time.desc()).first()

        return {
            "total_requests": total_requests,
            "unique_cities": unique_cities,
            "most_popular_city": {
                "city": popular_city.city if popular_city else None,
                "requests_count": popular_city.count if popular_city else 0,
            },
            "last_request": {
                "city": last_request.city if last_request else None,
                "time": last_request.request_time.isoformat() if last_request else None,
            },
        }
