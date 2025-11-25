"""empty message

Revision ID: 3b56dd72fd71
Revises: d58be45280b9
Create Date: 2025-10-09 10:01:16.009603

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "3b56dd72fd71"
down_revision: Union[str, None] = "d58be45280b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE company_role_enum ADD VALUE 'admin'")


def downgrade() -> None:
    pass
