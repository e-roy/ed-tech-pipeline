"""add_music_tracks_table

Revision ID: cae2ad28fd17
Revises: 75f6ac6ecf0e
Create Date: 2025-11-16 14:38:44.196449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cae2ad28fd17'
down_revision: Union[str, Sequence[str], None] = '75f6ac6ecf0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create music_tracks table
    op.create_table(
        'music_tracks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('track_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('mood', sa.String(length=50), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('bpm', sa.Integer(), nullable=True),
        sa.Column('s3_url', sa.Text(), nullable=False),
        sa.Column('license_type', sa.String(length=100), nullable=True),
        sa.Column('attribution', sa.Text(), nullable=True),
        sa.Column('suitable_for', sa.ARRAY(sa.String(length=255)), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('track_id')
    )

    # Add music columns to sessions table
    op.add_column('sessions', sa.Column('music_track_id', sa.String(length=255), nullable=True))
    op.add_column('sessions', sa.Column('music_s3_url', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('music_volume', sa.Float(), server_default='0.15', nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove music columns from sessions table
    op.drop_column('sessions', 'music_volume')
    op.drop_column('sessions', 'music_s3_url')
    op.drop_column('sessions', 'music_track_id')

    # Drop music_tracks table
    op.drop_table('music_tracks')
