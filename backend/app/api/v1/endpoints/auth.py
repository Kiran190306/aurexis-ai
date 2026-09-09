from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from datetime import datetime, timedelta
from typing import Any

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    get_current_user_id,
)
from app.core.config import settings
from app.schemas.auth import UserRegister, UserLogin, Token, TokenRefresh, UserResponse
from app.models.user import User, Session as UserSession
from app.models.user import UserRole

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)) -> User:
    """Register a new user."""
    logger.info(f"Registration attempt for email: {user_data.email}")
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.user,
        is_active=True,
        is_verified=False,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"New user registered: {user.email}")
    
    return user


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    """Authenticate user and return tokens."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked",
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Create session
    session = UserSession(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    
    # Update last login
    user.last_login = datetime.utcnow()  # type: ignore[assignment]
    user.failed_login_attempts = 0  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)) -> Token:
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(token_data.refresh_token)
        
        # Verify token type
        if not verify_token_type(payload, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        user_id = int(payload.get("sub") or 0)
        
        # Find user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        # Verify refresh token in database
        result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.refresh_token == token_data.refresh_token,
                UserSession.is_active == True,
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Create new tokens
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Update session
        session.token = access_token
        session.refresh_token = new_refresh_token
        
        await db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token",
        )


@router.post("/logout")
async def logout(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Logout user and invalidate session."""
    # Invalidate all sessions for user
    result = await db.execute(
        select(UserSession).where(UserSession.user_id == current_user_id)
    )
    sessions = result.scalars().all()
    
    for session in sessions:
        session.is_active = False  # type: ignore[assignment]
    
    await db.commit()
    
    logger.info(f"User logged out: {current_user_id}")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current user information."""
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user  # type: ignore[no-any-return]
