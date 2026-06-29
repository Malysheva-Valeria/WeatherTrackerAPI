"""Add favorite_cities table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-29 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'favorite_cities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'city', name='uq_favorite_user_city'),
    )
    op.create_index(op.f('ix_favorite_cities_id'), 'favorite_cities', ['id'], unique=False)
    op.create_index(op.f('ix_favorite_cities_user_id'), 'favorite_cities', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_favorite_cities_user_id'), table_name='favorite_cities')
    op.drop_index(op.f('ix_favorite_cities_id'), table_name='favorite_cities')
    op.drop_table('favorite_cities')
