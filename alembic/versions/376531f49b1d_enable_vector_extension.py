"""enable_vector_extension

Revision ID: 376531f49b1d
Revises: 0e8f331f6b9d
Create Date: 2026-04-14 14:42:52.385145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '376531f49b1d'
down_revision: Union[str, Sequence[str], None] = '0e8f331f6b9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP EXTENSION IF EXISTS vector')
