"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
# For Neon/SSL connections, configure connect_args to handle SSL without certificate files
connect_args = {}
if "neon" in settings.DATABASE_URL.lower() or "sslmode=require" in settings.DATABASE_URL.lower():
    # For Neon databases, use SSL but don't require certificate files
    # psycopg will use system defaults or skip certificate verification
    connect_args = {
        "sslmode": "require",
        # Don't specify certificate paths - let psycopg use defaults or skip
    }

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args if connect_args else {}
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
