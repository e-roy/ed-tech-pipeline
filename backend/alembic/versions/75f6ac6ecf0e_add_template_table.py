"""add_template_table

Revision ID: 75f6ac6ecf0e
Revises: 5576bd5530cf
Create Date: 2025-11-16 09:44:18.405507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75f6ac6ecf0e'
down_revision: Union[str, Sequence[str], None] = '5576bd5530cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('templates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('template_id', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('keywords', sa.JSON(), nullable=False),
    sa.Column('psd_url', sa.String(length=500), nullable=True),
    sa.Column('preview_url', sa.String(length=500), nullable=False),
    sa.Column('editable_layers', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('template_id')
    )
    op.create_index(op.f('ix_templates_id'), 'templates', ['id'], unique=False)
    op.create_index(op.f('ix_templates_template_id'), 'templates', ['template_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_templates_template_id'), table_name='templates')
    op.drop_index(op.f('ix_templates_id'), table_name='templates')
    op.drop_table('templates')
