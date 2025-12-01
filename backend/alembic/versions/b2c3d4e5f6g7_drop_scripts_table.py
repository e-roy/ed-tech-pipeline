"""drop_scripts_table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-01 00:00:00.000000

Scripts table is no longer needed - script data is now stored in
video_session.generated_script column instead.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the scripts table - script data now stored in video_session.generated_script."""
    # Use raw SQL with IF EXISTS to handle cases where table/index don't exist
    op.execute("DROP INDEX IF EXISTS ix_scripts_id")
    op.execute("DROP TABLE IF EXISTS scripts")


def downgrade() -> None:
    """Recreate scripts table if needed."""
    op.create_table('scripts',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hook', sa.JSON(), nullable=False),
        sa.Column('concept', sa.JSON(), nullable=False),
        sa.Column('process', sa.JSON(), nullable=False),
        sa.Column('conclusion', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scripts_id'), 'scripts', ['id'], unique=False)
