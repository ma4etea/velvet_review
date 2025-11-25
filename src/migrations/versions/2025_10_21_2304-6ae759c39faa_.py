"""empty message

Revision ID: 6ae759c39faa
Revises: fdab75bf5f3a
Create Date: 2025-10-21 23:04:57.403104

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision: str = "6ae759c39faa"
down_revision: Union[str, None] = "fdab75bf5f3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Добавляем новую колонку title как nullable
    op.add_column("stores", sa.Column("title", sa.String(length=255), nullable=True))

    # 2. Временный объект таблицы для UPDATE
    stores_table = table(
        "stores",
        column("name", sa.String),
        column("title", sa.String),
    )

    # 3. Копируем данные из name в title
    op.execute(stores_table.update().values(title=stores_table.c.name))

    # 4. Делаем колонку title NOT NULL
    op.alter_column("stores", "title", nullable=False)

    # 5. Создаём уникальный constraint на title
    op.create_unique_constraint("unique_constraint_title", "stores", ["title"])

    # 6. Удаляем старую колонку name
    op.drop_column("stores", "name")


def downgrade() -> None:
    # 1. Восстанавливаем колонку name
    op.add_column(
        "stores",
        sa.Column("name", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    )

    # 2. Копируем обратно данные из title в name
    stores_table = table(
        "stores",
        column("name", sa.String),
        column("title", sa.String),
    )
    op.execute(stores_table.update().values(name=stores_table.c.title))

    # 3. Удаляем уникальный constraint и колонку title
    op.drop_constraint("unique_constraint_title", "stores", type_="unique")
    op.drop_column("stores", "title")
