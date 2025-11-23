"""
Database configuration and session management.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Get DATABASE_URL from Secrets Manager first, then fall back to environment variable
# This allows production (ECS) to use Secrets Manager while local dev uses .env file
database_url = None

# Try to get from AWS Secrets Manager first
try:
    from app.services.secrets import get_secret
    try:
        database_url = get_secret("pipeline/database-url")
        logger.info("Retrieved DATABASE_URL from AWS Secrets Manager")
    except Exception as e:
        # Secrets Manager not available or secret doesn't exist - fall back to env var
        logger.debug(f"Could not retrieve DATABASE_URL from Secrets Manager: {e}, falling back to environment variable")
        database_url = None
except ImportError:
    # Secrets module not available (shouldn't happen, but handle gracefully)
    logger.debug("Secrets module not available, using environment variable")
    database_url = None
except Exception:
    # Any other error - fall back to env var
    database_url = None

# Fall back to environment variable if Secrets Manager didn't work
if not database_url:
    database_url = settings.DATABASE_URL
    logger.debug("Using DATABASE_URL from environment variable")

# Validate that we have a database URL
if not database_url:
    raise ValueError("DATABASE_URL is not configured. Set it in AWS Secrets Manager (pipeline/database-url) or environment variable (DATABASE_URL)")

# Create SQLAlchemy engine
# For Neon/SSL connections, configure SSL via connect_args to avoid certificate file requirements
connect_args = {}

# If using Neon database, configure SSL without requiring certificate files
if database_url and "neon" in database_url.lower():
    import re

    # Remove ALL query parameters from URL (we'll set them via connect_args)
    # This prevents parameters like channel_binding from being interpreted as part of the database name
    database_url = re.sub(r"\?.*$", "", database_url)

    connect_args = {
        "sslmode": "require",
        "sslrootcert": "/etc/pki/tls/certs/ca-bundle.crt",
        # Disable attempts to read ~/.postgresql certificates (blocked by ProtectHome)
        "sslcert": "",
        "sslkey": "",
    }

# Fallback: ensure SSL is at least preferred for PostgreSQL connections
if database_url and database_url.startswith("postgresql") and "sslmode" not in connect_args:
    connect_args["sslmode"] = "prefer"

engine = create_engine(
    database_url,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    Usage in FastAPI routes:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    import logging
    logger = logging.getLogger(__name__)
    
    db = None
    try:
        db = SessionLocal()
        # Test the connection
        from sqlalchemy import text as sql_text
        db.execute(sql_text("SELECT 1"))
        yield db
    except Exception as e:
        logger.exception(f"Database connection error: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()


def init_db():
    """
    Initialize database - create all tables.

    This is used for development. In production, use Alembic migrations.
    """
    from app.models import database  # Import models to register them
    Base.metadata.create_all(bind=engine)
