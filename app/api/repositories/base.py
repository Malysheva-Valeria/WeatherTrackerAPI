"""
Базовий репозиторій: інкапсулює доступ до БД для конкретної моделі.

Репозиторії існують, щоб роутери та сервіси не працювали з SQLAlchemy-сесією
напряму — уся робота з БД зосереджена тут.
"""
from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from app.api.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Узагальнений репозиторій з типовими CRUD-операціями."""

    model: Type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def get(self, obj_id: int) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == obj_id).first()

    def list(self) -> List[ModelType]:
        return self.db.query(self.model).all()

    def add(self, obj: ModelType, *, commit: bool = True) -> ModelType:
        self.db.add(obj)
        if commit:
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType, *, commit: bool = True) -> None:
        self.db.delete(obj)
        if commit:
            self.db.commit()
