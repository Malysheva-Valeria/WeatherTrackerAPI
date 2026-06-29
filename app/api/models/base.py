"""
Базова модель для всіх моделей WeatherTracker API
"""
from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class BaseModel(Base):
    """
    Абстрактна базова модель з common полями
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self):
        """Конвертація моделі в словник"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    @classmethod
    def get_table_name(cls):
        """Отримання назви таблиці"""
        return cls.__tablename__
