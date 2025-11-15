"""
Authentication routes - simplified for MVP.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import hashlib

from app.database import get_db
from app.config import get_settings
from app.models.database import User

router = APIRouter()
settings = get_settings()

# Password hashing - using SHA256 for MVP simplicity
# In production, use bcrypt or argon2

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class TokenExchangeRequest(BaseModel):
    """Request model for token exchange endpoint."""
    email: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """
    Hash a password using SHA256.

    NOTE: This is simplified for MVP. In production, use bcrypt/argon2.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def get_or_create_demo_user(db: Session) -> User:
    """Get or create the demo user for MVP testing."""
    demo_email = "demo@example.com"
    demo_password = "demo123"

    user = db.query(User).filter(User.email == demo_email).first()
    if not user:
        # Create demo user
        hashed_password = get_password_hash(demo_password)
        user = User(email=demo_email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Simplified login endpoint for MVP.

    Accepts:
    - username: demo@example.com
    - password: demo123

    Returns JWT access token.
    """
    # For MVP, we only support demo user
    demo_user = get_or_create_demo_user(db)

    # Verify credentials
    if form_data.username != demo_user.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, demo_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": demo_user.email},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user from JWT token.

    Use this in protected endpoints:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            ...
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception

    return user


@router.post("/exchange", response_model=Token)
async def exchange_token(
    request: TokenExchangeRequest,
    db: Session = Depends(get_db)
):
    """
    Exchange NextAuth session for backend JWT token.
    
    This endpoint allows the frontend to exchange a NextAuth session (identified by email)
    for a backend JWT token. This keeps the backend independent of NextAuth while
    allowing seamless authentication flow.
    
    Args:
        request: TokenExchangeRequest containing user email from NextAuth session
        
    Returns:
        JWT access token compatible with backend authentication
        
    Raises:
        HTTPException: If user doesn't exist in backend database
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {request.email} not found in backend database"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
