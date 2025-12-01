"""
Simplified authentication - trusts frontend NextAuth user info from headers.

For MVP/educational content only. Frontend handles authentication via NextAuth,
backend trusts user ID/email sent in request headers.

Backend reads from the auth_user table managed by the frontend's NextAuth/Drizzle setup.
"""
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.database import User

logger = logging.getLogger(__name__)


async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from request headers (sent by authenticated frontend).

    Frontend includes these headers after NextAuth authentication:
    - X-User-Id: User's database ID (UUID) from NextAuth
    - X-User-Email: User's email from NextAuth session

    Users are created by NextAuth on the frontend. Backend only reads from auth_user.

    Args:
        x_user_id: User ID (UUID string) from header
        x_user_email: User email from header
        db: Database session

    Returns:
        User object from auth_user table

    Raises:
        HTTPException: If user headers missing or user not found
    """
    try:
        # Prefer looking up by ID if provided (more reliable)
        if x_user_id:
            logger.debug(f"Looking up user by ID: {x_user_id}")
            user = db.query(User).filter(User.id == x_user_id).first()
            if user:
                return user
            logger.warning(f"User not found by ID: {x_user_id}")

        # Fall back to email lookup
        if x_user_email:
            logger.debug(f"Looking up user by email: {x_user_email}")
            user = db.query(User).filter(User.email == x_user_email).first()
            if user:
                return user
            logger.warning(f"User not found by email: {x_user_email}")

        # No valid user found
        if not x_user_id and not x_user_email:
            logger.warning("Missing authentication headers")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing user authentication headers. Please ensure you're logged in."
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please ensure you're logged in on the frontend first."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )
