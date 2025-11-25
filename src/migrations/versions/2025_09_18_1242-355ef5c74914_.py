"""empty message

Revision ID: 355ef5c74914
Revises: dafe1017e250
Create Date: 2025-09-18 12:42:46.605677

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "355ef5c74914"
down_revision: Union[str, None] = "dafe1017e250"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("units", sa.Column("main_image_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "units", "unit_images", ["main_image_id"], ["id"])
    op.drop_column("units", "keys_image")


def downgrade() -> None:
    op.add_column(
        "units",
        sa.Column(
            "keys_image",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.drop_constraint(None, "units", type_="foreignkey")
    op.drop_column("units", "main_image_id")
