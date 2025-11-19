"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
# For Neon/SSL connections, modify connection string to avoid certificate file requirements
database_url = settings.DATABASE_URL

# If using Neon or SSL-required connection, modify sslmode to avoid certificate file lookups
if "neon" in database_url.lower():
    # Replace sslmode=require with sslmode=prefer (will use SSL if available, but won't fail without certs)
    # Or use sslmode=require with sslcert='' to disable certificate file lookup
    import re
    if "sslmode=require" in database_url:
        # Replace with prefer to avoid certificate file requirements
        database_url = re.sub(r"sslmode=require", "sslmode=prefer", database_url, flags=re.IGNORECASE)
    elif "?" in database_url and "sslmode" not in database_url.lower():
        # Add sslmode=prefer if not present
        database_url = database_url + "&sslmode=prefer" if "?" in database_url else database_url + "?sslmode=prefer"

engine = create_engine(
    database_url,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20
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
