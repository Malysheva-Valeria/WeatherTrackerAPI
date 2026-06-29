"""
Favorites Router — управління улюбленими містами користувача.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.models.user import User
from app.api.repositories.favorite_repository import FavoriteCityRepository
from app.api.schemas.base import MessageResponse
from app.api.schemas.favorite import FavoriteCityCreate, FavoriteCityResponse, FavoriteWeatherItem
from app.api.schemas.weather import CurrentWeatherResponse
from app.api.services.weather_service import get_weather_service
from app.dependencies import get_current_active_user, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("", response_model=FavoriteCityResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
        body: FavoriteCityCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Додати місто в обране (не можна додати двічі)."""
    repo = FavoriteCityRepository(db)
    city = body.city.strip()

    if repo.find_by_city(current_user.id, city):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Місто вже в обраному",
        )

    favorite = repo.add_city(current_user.id, city)
    return FavoriteCityResponse.model_validate(favorite)


@router.get("", response_model=List[FavoriteCityResponse])
async def list_favorites(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Список улюблених міст користувача."""
    favorites = FavoriteCityRepository(db).list_for_user(current_user.id)
    return [FavoriteCityResponse.model_validate(f) for f in favorites]


@router.delete("/{favorite_id}", response_model=MessageResponse)
async def remove_favorite(
        favorite_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Видалити місто з обраного."""
    repo = FavoriteCityRepository(db)
    favorite = repo.get_for_user(current_user.id, favorite_id)
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Улюблене місто не знайдено",
        )
    city = favorite.city
    repo.delete(favorite)
    return MessageResponse(message=f"Місто '{city}' видалено з обраного")


@router.get("/weather", response_model=List[FavoriteWeatherItem])
async def favorites_weather(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Поточна погода для всіх улюблених міст (одним запитом)."""
    favorites = FavoriteCityRepository(db).list_for_user(current_user.id)
    weather_service = get_weather_service()

    items: List[FavoriteWeatherItem] = []
    for favorite in favorites:
        try:
            raw = await weather_service.get_current_weather(favorite.city)
            formatted = weather_service.format_weather_response(raw)
            items.append(
                FavoriteWeatherItem(city=favorite.city, weather=CurrentWeatherResponse(**formatted))
            )
        except ValueError as exc:
            items.append(FavoriteWeatherItem(city=favorite.city, error=str(exc)))
        except Exception:
            logger.exception("Помилка отримання погоди для улюбленого міста %s", favorite.city)
            items.append(FavoriteWeatherItem(city=favorite.city, error="Внутрішня помилка"))

    return items
