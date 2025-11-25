"""empty message

Revision ID: 8d76cd7abc3c
Revises: 8fc070dc489b
Create Date: 2025-09-26 13:38:35.062128

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8d76cd7abc3c"
down_revision: Union[str, None] = "8fc070dc489b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f("unit_images_unit_id_fkey"), "unit_images", type_="foreignkey")
    op.create_foreign_key(None, "unit_images", "units", ["unit_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.drop_constraint(None, "unit_images", type_="foreignkey")
    op.create_foreign_key(
        op.f("unit_images_unit_id_fkey"), "unit_images", "units", ["unit_id"], ["id"]
    )
