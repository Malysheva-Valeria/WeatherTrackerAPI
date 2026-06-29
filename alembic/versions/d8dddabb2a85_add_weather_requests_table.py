"""Add weather_requests table

Revision ID: d8dddabb2a85
Revises: ccb148558038
Create Date: 2025-08-19 22:10:11.359031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8dddabb2a85'
down_revision: Union[str, Sequence[str], None] = 'ccb148558038'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Історичний плейсхолдер: таблиця weather_requests фактично створюється
    в наступній міграції (fbef48a236e0) разом з forecast-таблицями.
    """
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
