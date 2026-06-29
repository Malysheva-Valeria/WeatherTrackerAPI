"""
AuditService — запис та читання журналу аудиту чутливих дій.
"""
import logging
from typing import List, Optional

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.models.audit import AuditLog
from app.database import get_db

logger = logging.getLogger(__name__)


def client_ip(request: Optional[Request]) -> Optional[str]:
    """Безпечно дістати IP клієнта із запиту."""
    if request is None or request.client is None:
        return None
    return request.client.host


class AuditService:
    """Сервіс журналу аудиту."""

    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        action: str,
        *,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        """Записати подію. Помилка аудиту не повинна валити основний запит."""
        try:
            self.db.add(
                AuditLog(action=action, user_id=user_id, ip_address=ip_address, detail=detail)
            )
            self.db.commit()
        except Exception:
            logger.exception("Не вдалося записати подію аудиту: %s", action)
            self.db.rollback()

    def list_for_user(self, user_id: int, *, limit: int = 50) -> List[AuditLog]:
        """Останні записи журналу конкретного користувача."""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(db)
