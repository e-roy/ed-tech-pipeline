"""
Simplified authentication - trusts frontend NextAuth user info from headers.

For MVP/educational content only. Frontend handles authentication via NextAuth,
backend trusts user ID/email sent in request headers.

Auth is handled by frontend's auth_user table - no backend users table needed.
"""
from fastapi import Header, HTTPException, status
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CurrentUser:
    """
    User info from frontend auth headers.

    Represents the authenticated user from frontend's auth_user table.
    No database lookup needed - we trust the frontend's NextAuth session.
    """
    id: str  # auth_user.id (UUID string from frontend)
    email: str  # auth_user.email


async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
) -> CurrentUser:
    """
    Get current user from request headers (sent by authenticated frontend).

    Frontend includes these headers after NextAuth authentication:
    - X-User-Id: User's auth_user.id (UUID string) from NextAuth
    - X-User-Email: User's email from NextAuth session

    This replaces JWT authentication for simplicity in MVP.
    Assumes frontend is trusted and handles authentication properly.

    No database lookup is performed - we trust the frontend's auth headers.
    The user ID is the UUID from frontend's auth_user table.

    Args:
        x_user_id: User ID from header (auth_user.id UUID string)
        x_user_email: User email from header

    Returns:
        CurrentUser object with id and email

    Raises:
        HTTPException: If required user headers are missing
    """
    try:
        if not x_user_email:
            logger.warning("Missing X-User-Email header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing user authentication headers. Please ensure you're logged in."
            )

        if not x_user_id:
            logger.warning("Missing X-User-Id header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing user authentication headers. Please ensure you're logged in."
            )

        logger.debug(f"Authenticated user: id={x_user_id}, email={x_user_email}")

        return CurrentUser(id=x_user_id, email=x_user_email)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )
