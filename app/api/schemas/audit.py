"""Pydantic схеми для журналу аудиту."""
from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from app.api.schemas.base import BaseSchema


class AuditLogResponse(BaseSchema):
    """Запис журналу аудиту у відповіді API."""
    id: int
    action: str
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
