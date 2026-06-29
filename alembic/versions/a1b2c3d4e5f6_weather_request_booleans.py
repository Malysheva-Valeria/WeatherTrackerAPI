"""Convert weather_requests.is_cached/is_mock from String to Boolean

Revision ID: a1b2c3d4e5f6
Revises: fbef48a236e0
Create Date: 2026-06-29 00:00:00.000000

Примітка: попередні міграції в цьому проєкті — порожні (схема історично
створювалась через Base.metadata.create_all), тому ця міграція написана
захищено: вона перевіряє наявність таблиці/колонок і застосовує зміни лише
там, де це доречно. Завдяки цьому `alembic upgrade head` безпечний незалежно
від того, як саме було створено схему.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fbef48a236e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "weather_requests"
BOOL_COLUMNS = ("is_cached", "is_mock")


def _existing_columns() -> set:
    bind = op.get_bind()
    inspector = inspect(bind)
    if TABLE not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(TABLE)}


def _column_types() -> dict:
    """Назва колонки -> рядкове представлення її типу (для перевірки Boolean)."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if TABLE not in inspector.get_table_names():
        return {}
    return {col["name"]: str(col["type"]).upper() for col in inspector.get_columns(TABLE)}


def upgrade() -> None:
    """String(10) -> Boolean для is_cached/is_mock (no-op, якщо вже Boolean)."""
    bind = op.get_bind()
    columns = _existing_columns()
    types = _column_types()
    is_postgres = bind.dialect.name == "postgresql"

    for column in BOOL_COLUMNS:
        if column not in columns:
            continue
        # Якщо колонка вже Boolean (її створили одразу таким типом) — пропускаємо.
        if "BOOL" in types.get(column, ""):
            continue
        if is_postgres:
            # Явний CAST зі строкових значень ('true'/'false'/'') у boolean
            op.execute(
                f"ALTER TABLE {TABLE} "
                f"ALTER COLUMN {column} DROP DEFAULT"
            )
            op.execute(
                f"ALTER TABLE {TABLE} "
                f"ALTER COLUMN {column} TYPE BOOLEAN "
                f"USING (CASE WHEN lower({column}) IN ('true', 't', '1') THEN true ELSE false END)"
            )
            op.execute(
                f"ALTER TABLE {TABLE} "
                f"ALTER COLUMN {column} SET DEFAULT false"
            )
            op.execute(
                f"ALTER TABLE {TABLE} "
                f"ALTER COLUMN {column} SET NOT NULL"
            )
        else:
            with op.batch_alter_table(TABLE) as batch_op:
                batch_op.alter_column(
                    column,
                    type_=sa.Boolean(),
                    existing_type=sa.String(length=10),
                    nullable=False,
                    server_default=sa.false(),
                )


def downgrade() -> None:
    """No-op: у канонічному ланцюзі колонки створюються як Boolean одразу
    (fbef48a236e0), а скасування таблиці робить її downgrade. Повертати тип
    назад до String немає сенсу й це лише зіпсувало б схему."""
    pass
