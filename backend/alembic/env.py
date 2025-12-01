from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import our database configuration and models
from app.database import Base
from app.config import get_settings
from app.models import database  # Import models to register them

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get settings from our config
settings = get_settings()

# Set the database URL from our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Set target metadata to our Base metadata
target_metadata = Base.metadata

# Tables managed by the frontend (NextAuth/Drizzle) - Alembic should NOT touch these
FRONTEND_MANAGED_TABLES = {
    'auth_user',
    'auth_account',
    'auth_session',
    'auth_verification_token',
    'video_session',
    'video_asset',
    'video_conversation_message',
    'webhook_log',
    'error_report_report',
}


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter function for Alembic autogenerate.
    Excludes tables managed by the frontend.
    """
    if type_ == "table" and name in FRONTEND_MANAGED_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
