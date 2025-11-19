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
    # Remove any trailing & or ? if they become empty
    database_url = re.sub(r"[&?]$", "", database_url)
    
    # Configure SSL via connect_args - this bypasses psycopg's certificate file lookup
    # For Neon, we need SSL but don't need client certificates
    connect_args = {
        "sslmode": "require",
        # Don't specify sslcert/sslkey - psycopg will use SSL without client certs
    }

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
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
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
