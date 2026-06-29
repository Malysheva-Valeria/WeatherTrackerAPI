"""
Репозиторій для улюблених міст користувача.
"""
from typing import List, Optional

from app.api.models.favorite_city import FavoriteCity
from app.api.repositories.base import BaseRepository


class FavoriteCityRepository(BaseRepository[FavoriteCity]):
    """Доступ до даних улюблених міст."""

    model = FavoriteCity

    def list_for_user(self, user_id: int) -> List[FavoriteCity]:
        return (
            self.db.query(FavoriteCity)
            .filter(FavoriteCity.user_id == user_id)
            .order_by(FavoriteCity.created_at.desc())
            .all()
        )

    def get_for_user(self, user_id: int, favorite_id: int) -> Optional[FavoriteCity]:
        return (
            self.db.query(FavoriteCity)
            .filter(FavoriteCity.id == favorite_id, FavoriteCity.user_id == user_id)
            .first()
        )

    def find_by_city(self, user_id: int, city: str) -> Optional[FavoriteCity]:
        return (
            self.db.query(FavoriteCity)
            .filter(FavoriteCity.user_id == user_id, FavoriteCity.city.ilike(city))
            .first()
        )

    def add_city(self, user_id: int, city: str, country: Optional[str] = None) -> FavoriteCity:
        favorite = FavoriteCity(user_id=user_id, city=city, country=country)
        return self.add(favorite)
