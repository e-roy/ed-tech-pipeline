"""
Diagnostic endpoints for verifying production configuration.
These endpoints provide information about database connections and configuration
without exposing sensitive credentials.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.database import get_db, engine
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


def sanitize_database_url(url: str) -> str:
    """
    Sanitize database URL to hide credentials while showing connection info.
    
    Example:
        postgresql+psycopg://user:pass@host:port/db
        -> postgresql+psycopg://user:***@host:port/db
    """
    if not url:
        return "Not configured"
    
    try:
        # Parse the URL
        if "://" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                auth, host_part = rest.split("@", 1)
                if ":" in auth:
                    user, _ = auth.split(":", 1)
                    return f"{scheme}://{user}:***@{host_part}"
                else:
                    return f"{scheme}://{auth}:***@{host_part}"
            else:
                return f"{scheme}://***@{rest}"
        return "***"
    except Exception:
        return "***"


@router.get("/database")
async def get_database_info(db: Session = Depends(get_db)):
    """
    Get database connection information (sanitized).
    
    Returns information about the database connection without exposing credentials.
    """
    settings = get_settings()
    
    # Get the actual database URL being used (from engine, which may have come from Secrets Manager)
    # The engine.url shows the actual connection string being used
    actual_database_url = None
    if hasattr(engine, 'url'):
        actual_database_url = str(engine.url)
    else:
        # Fallback to settings if engine.url not available
        actual_database_url = settings.DATABASE_URL
    
    # Sanitize the URL
    sanitized_url = sanitize_database_url(actual_database_url)
    
    # Extract connection info
    # Determine source: if actual_database_url differs from settings.DATABASE_URL, it likely came from Secrets Manager
    # Note: This is a best-effort detection - we can't be 100% certain without storing the source
    source = "unknown"
    if actual_database_url:
        if actual_database_url != settings.DATABASE_URL:
            source = "likely_secrets_manager"  # Different from env var, likely from Secrets Manager
        else:
            source = "environment_variable"  # Matches env var
    
    connection_info = {
        "url_sanitized": sanitized_url,
        "is_neon": "neon" in actual_database_url.lower() if actual_database_url else False,
        "has_ssl": "sslmode" in actual_database_url.lower() if actual_database_url else False,
        "engine_url": str(engine.url).split("@")[-1] if hasattr(engine, 'url') else None,
        "source": source,
    }
    
    # Test connection
    connection_status = {
        "connected": False,
        "error": None
    }
    
    try:
        result = db.execute(sql_text("SELECT 1 as test"))
        result.fetchone()
        connection_status["connected"] = True
        
        # Get database name and version
        db_info = db.execute(sql_text("SELECT current_database() as db_name, version() as version")).fetchone()
        if db_info:
            connection_info["database_name"] = db_info[0] if hasattr(db_info, '_mapping') else db_info[0]
            version = db_info[1] if hasattr(db_info, '_mapping') else db_info[1]
            connection_info["database_version"] = version.split(",")[0] if version else None
        
        # Check if video_session table exists
        table_check = db.execute(sql_text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'video_session'
            )
        """)).scalar()
        connection_info["video_session_table_exists"] = table_check
        
        # Count rows in video_session
        if table_check:
            row_count = db.execute(sql_text("SELECT COUNT(*) FROM video_session")).scalar()
            connection_info["video_session_row_count"] = row_count
        
    except Exception as e:
        connection_status["connected"] = False
        connection_status["error"] = str(e)
        logger.error(f"Database connection test failed: {e}")
    
    return {
        "connection_info": connection_info,
        "connection_status": connection_status,
        "agent2_uses_same_db": True,  # Agent2 uses get_db() or receives db parameter
        "agent4_uses_same_db": True,  # Agent4 uses get_db() or receives db parameter
    }


@router.get("/database/test-query")
async def test_database_query(
    session_id: str = None,
    user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Test the exact query pattern that Agent2 and Agent4 use.
    
    This verifies that the database connection works with the same query pattern
    that the agents use.
    """
    if not session_id or not user_id:
        return {
            "error": "session_id and user_id are required",
            "usage": "/api/diagnostics/database/test-query?session_id=xxx&user_id=xxx"
        }
    
    try:
        # Use the exact same query pattern as Agent2 and Agent4
        result = db.execute(
            sql_text(
                "SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"
            ),
            {"session_id": session_id, "user_id": user_id},
        ).fetchone()
        
        if result:
            # Convert to dict (same as agents do)
            if hasattr(result, "_mapping"):
                data = dict(result._mapping)
            else:
                data = {
                    "id": getattr(result, "id", None),
                    "user_id": getattr(result, "user_id", None),
                    "topic": getattr(result, "topic", None),
                    "generated_script": getattr(result, "generated_script", None),
                }
            
            # Check if generated_script exists and is valid (same logic as agents)
            generated_script = data.get("generated_script")
            has_generated_script = generated_script is not None
            
            # Try to extract script structure (same as Agent2 does)
            script_valid = False
            if has_generated_script and isinstance(generated_script, dict):
                # Check if it has the required structure
                if "hook" in generated_script or "script" in generated_script or "segments" in generated_script:
                    script_valid = True
            
            return {
                "success": True,
                "found": True,
                "has_generated_script": has_generated_script,
                "script_is_valid": script_valid,
                "fields_retrieved": list(data.keys()),
                "message": "Query successful - matches Agent2/Agent4 query pattern"
            }
        else:
            return {
                "success": True,
                "found": False,
                "message": f"Session {session_id} not found for user {user_id}"
            }
            
    except Exception as e:
        logger.error(f"Database test query failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

