"""add_verification_fields

Revision ID: a1b2c3d4e5f6
Revises: cae2ad28fd17
Create Date: 2025-11-22 00:00:00.000000

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
    # Add verification columns to assets table
    op.add_column('assets', sa.Column('verification_status', sa.String(length=50), nullable=True))
    op.add_column('assets', sa.Column('verification_data', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))

    # Add verification columns to sessions table for final video
    op.add_column('sessions', sa.Column('final_video_verification_status', sa.String(length=50), nullable=True))
    op.add_column('sessions', sa.Column('final_video_verification_data', sa.JSON(), nullable=True))
    op.add_column('sessions', sa.Column('final_video_verified_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove verification columns from sessions table
    op.drop_column('sessions', 'final_video_verified_at')
    op.drop_column('sessions', 'final_video_verification_data')
    op.drop_column('sessions', 'final_video_verification_status')

    # Remove verification columns from assets table
    op.drop_column('assets', 'verified_at')
    op.drop_column('assets', 'verification_data')
    op.drop_column('assets', 'verification_status')
