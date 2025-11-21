"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
# For Neon/SSL connections, configure SSL via connect_args to avoid certificate file requirements
database_url = settings.DATABASE_URL
connect_args = {}

# If using Neon database, configure SSL without requiring certificate files
if "neon" in database_url.lower():
    import re

    # Remove sslmode from URL if present (we'll set it via connect_args)
    database_url = re.sub(r"[&?]sslmode=[^&]*", "", database_url, flags=re.IGNORECASE)
    database_url = re.sub(r"[&?]$", "", database_url)

    connect_args = {
        "sslmode": "require",
        "sslrootcert": "/etc/pki/tls/certs/ca-bundle.crt",
        # Disable attempts to read ~/.postgresql certificates (blocked by ProtectHome)
        "sslcert": "",
        "sslkey": "",
    }

# Fallback: ensure SSL is at least preferred for PostgreSQL connections
if database_url.startswith("postgresql") and "sslmode" not in connect_args:
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
