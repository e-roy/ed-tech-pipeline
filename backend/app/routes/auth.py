"""
Simplified authentication - trusts frontend NextAuth user info from headers.

For MVP/educational content only. Frontend handles authentication via NextAuth,
backend trusts user ID/email sent in request headers.
"""
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.database import User


async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    x_user_email: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from request headers (sent by authenticated frontend).

    Frontend includes these headers after NextAuth authentication:
    - X-User-Id: User's database ID from NextAuth
    - X-User-Email: User's email from NextAuth session

    This replaces JWT authentication for simplicity in MVP.
    Assumes frontend is trusted and handles authentication properly.

    Args:
        x_user_id: User ID from header
        x_user_email: User email from header
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If user headers missing or user not found
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not x_user_email:
            logger.warning("Missing X-User-Email header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing user authentication headers. Please ensure you're logged in."
            )

        logger.debug(f"Getting user for email: {x_user_email}")
        
        # Find or create user by email
        user = db.query(User).filter(User.email == x_user_email).first()

        if user is None:
            logger.info(f"Creating new user for email: {x_user_email}")
            # Auto-create user for new OAuth users (Google, Discord, etc.)
            # Set placeholder password since OAuth users don't have passwords
            import bcrypt
            placeholder_password = bcrypt.hashpw(f"oauth_{x_user_email}".encode(), bcrypt.gensalt()).decode()
            user = User(email=x_user_email, hashed_password=placeholder_password)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created user: {user.id}")

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )
