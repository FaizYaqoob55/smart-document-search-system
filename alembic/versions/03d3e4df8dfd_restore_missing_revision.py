"""restore missing revision 03d3e4df8dfd

Revision ID: 03d3e4df8dfd
Revises: d7e1d8d6729f
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '03d3e4df8dfd'
down_revision: Union[str, Sequence[str], None] = 'd7e1d8d6729f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
