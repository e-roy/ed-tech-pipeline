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
    if not x_user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user authentication headers. Please ensure you're logged in."
        )

    # Find or create user by email
    user = db.query(User).filter(User.email == x_user_email).first()

    if user is None:
        # Auto-create user for new OAuth users (Google, Discord, etc.)
        # Set placeholder password since OAuth users don't have passwords
        import bcrypt
        placeholder_password = bcrypt.hashpw(f"oauth_{x_user_email}".encode(), bcrypt.gensalt()).decode()
        user = User(email=x_user_email, hashed_password=placeholder_password)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
