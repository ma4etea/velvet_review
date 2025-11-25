"""empty message

Revision ID: fdab75bf5f3a
Revises: 3b56dd72fd71
Create Date: 2025-10-09 13:38:41.331863

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "fdab75bf5f3a"
down_revision: Union[str, None] = "3b56dd72fd71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "unique_constraint_user_store", "role_user_in_store", ["user_id", "store_id"]
    )
    op.execute("ALTER TYPE role_user_in_store_enum ADD VALUE IF NOT EXISTS 'manager'")
    op.execute("ALTER TYPE role_user_in_store_enum ADD VALUE IF NOT EXISTS 'viewer'")


def downgrade() -> None:
    op.drop_constraint("unique_constraint_user_store", "role_user_in_store", type_="unique")
