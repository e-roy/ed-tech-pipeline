"""refactor_sessions_use_auth_user

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-01 12:00:00.000000

Refactors the sessions table to:
1. Use auth_user.id (string UUID) instead of users.id (integer)
2. Remove redundant config columns (prompt, video_prompt, options, etc.)
3. Drop the users table - auth is now handled by frontend's auth_user

video_session is now the source of truth for content (scripts, facts, etc.)
sessions is the source of truth for media production (video generation, music, assets)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Refactor sessions to use auth_user and remove redundant columns.

    Steps:
    1. Drop foreign key constraint on sessions.user_id
    2. Alter sessions.user_id from Integer to String(255)
    3. Drop redundant config columns from sessions
    4. Drop foreign key constraints referencing users table
    5. Drop the users table
    """
    # Step 1: Drop foreign key constraint on sessions.user_id
    op.drop_constraint('sessions_user_id_fkey', 'sessions', type_='foreignkey')

    # Step 2: Alter sessions.user_id from Integer to String(255)
    # Note: This requires data migration - existing integer IDs need to be converted
    # For safety, we'll create a new column, migrate data, then drop old column
    op.add_column('sessions', sa.Column('user_id_new', sa.String(length=255), nullable=True))

    # Migrate existing integer user_ids to string format (temporary - will need manual data migration)
    op.execute("UPDATE sessions SET user_id_new = CAST(user_id AS VARCHAR(255))")

    # Drop old user_id column and rename new one
    op.drop_column('sessions', 'user_id')
    op.alter_column('sessions', 'user_id_new', new_column_name='user_id', nullable=False)

    # Add index on user_id for query performance
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)

    # Step 3: Drop redundant config columns from sessions
    # These are now passed in API request body or stored in video_session
    op.drop_column('sessions', 'prompt')
    op.drop_column('sessions', 'video_prompt')
    op.drop_column('sessions', 'options')
    op.drop_column('sessions', 'clip_config')
    op.drop_column('sessions', 'text_config')
    op.drop_column('sessions', 'audio_config')

    # Step 4: Drop the users table (auth is handled by frontend's auth_user)
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')


def downgrade() -> None:
    """
    Restore users table and sessions config columns.

    WARNING: This will lose any user data stored in auth_user format.
    """
    # Recreate users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Restore config columns to sessions
    op.add_column('sessions', sa.Column('audio_config', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('sessions', sa.Column('text_config', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('sessions', sa.Column('clip_config', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('sessions', sa.Column('options', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('sessions', sa.Column('video_prompt', sa.Text(), nullable=True))
    op.add_column('sessions', sa.Column('prompt', sa.Text(), nullable=True))

    # Drop index on user_id
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')

    # Restore user_id as Integer with FK (will require manual data migration)
    op.add_column('sessions', sa.Column('user_id_old', sa.Integer(), nullable=True))
    op.drop_column('sessions', 'user_id')
    op.alter_column('sessions', 'user_id_old', new_column_name='user_id', nullable=False)
    op.create_foreign_key('sessions_user_id_fkey', 'sessions', 'users', ['user_id'], ['id'])
