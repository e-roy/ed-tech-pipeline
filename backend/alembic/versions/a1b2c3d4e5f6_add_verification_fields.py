"""add_verification_fields

Revision ID: a1b2c3d4e5f6
Revises: cae2ad28fd17
Create Date: 2025-11-22 00:00:00.000000

NOTE: Asset verification fields are now included in the initial_schema migration.
Session verification fields have been removed from the model (unused).
This migration is kept for backwards compatibility but is now a no-op.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'cae2ad28fd17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Asset verification fields are now in initial_schema migration
    # Session verification fields have been removed (unused)
    # This migration is a no-op for fresh installs
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # No-op - fields either in initial_schema or removed from model
    pass
