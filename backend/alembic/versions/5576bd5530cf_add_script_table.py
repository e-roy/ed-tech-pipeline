"""add_script_table

Revision ID: 5576bd5530cf
Revises: d492dd459bcb
Create Date: 2025-11-16 09:29:18.474773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5576bd5530cf'
down_revision: Union[str, Sequence[str], None] = 'd492dd459bcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_scripts_id'), table_name='scripts')
    op.drop_table('scripts')
