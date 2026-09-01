from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from loguru import logger

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings
from app.repositories.user import UserRepository, SessionRepository
from app.models.user import User, Session as UserSession
from app.schemas.auth import UserRegister, Token


class AuthService:
    """Service for authentication operations."""

    def __init__(self) -> None:
        self.user_repo = UserRepository(User)
        self.session_repo = SessionRepository(UserSession)

    async def register(
        self,
        db: AsyncSession,
        user_data: UserRegister,
    ) -> User:
        """Register a new user."""
        # Check if email exists
        existing_user = await self.user_repo.get_by_email(db, user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Check if username exists
        existing_user = await self.user_repo.get_by_username(db, user_data.username)
        if existing_user:
            raise ValueError("Username already taken")
        
        # Create user
        user = await self.user_repo.create(db, user_data)
        
        logger.info(f"User registered: {user.email}")
        return user

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Tuple[User, Token]:
        """Authenticate user and return tokens."""
        # Get user
        user = await self.user_repo.get_by_email(db, email)
        if not user:
            raise ValueError("Incorrect email or password")
        
        # Verify password
        if not verify_password(password, str(user.hashed_password)):
            # Increment failed login attempts
            await self.user_repo.increment_failed_login(db, int(user.id))
            raise ValueError("Incorrect email or password")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is inactive")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise ValueError("Account is temporarily locked")
        
        # Reset failed login attempts
        await self.user_repo.reset_failed_login(db, int(user.id))
        
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
        await db.commit()
        
        token_response = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
        logger.info(f"User logged in: {user.email}")
        return user, token_response

    async def refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> Token:
        """Refresh access token using refresh token."""
        from app.core.security import decode_token, verify_token_type
        
        try:
            payload = decode_token(refresh_token)
            
            # Verify token type
            if not verify_token_type(payload, "refresh"):
                raise ValueError("Invalid token type")
            
            user_id = int(payload.get("sub") or "0")
            
            # Get user
            user = await self.user_repo.get(db, user_id)
            if not user:
                raise ValueError("User not found")
            
            # Verify refresh token in database
            session = await self.session_repo.get_by_refresh_token(db, refresh_token)
            if not session:
                raise ValueError("Invalid refresh token")
            
            # Create new tokens
            access_token = create_access_token(
                data={"sub": str(user.id)},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
            
            # Update session
            session.token = access_token  # type: ignore[assignment]
            session.refresh_token = new_refresh_token  # type: ignore[assignment]
            
            await db.commit()
            
            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise ValueError("Could not refresh token")

    async def logout(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> bool:
        """Logout user and invalidate all sessions."""
        await self.user_repo.invalidate_all_sessions(db, user_id)
        logger.info(f"User logged out: {user_id}")
        return True

    async def logout_session(
        self,
        db: AsyncSession,
        session_id: int,
        user_id: int,
    ) -> bool:
        """Logout specific session."""
        session = await self.session_repo.get(db, session_id)
        if session and session.user_id == user_id:
            session.is_active = False  # type: ignore[assignment]
            await db.commit()
            return True
        return False

    async def get_current_user(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        """Get current user by ID."""
        return await self.user_repo.get(db, user_id)

    async def verify_oauth(
        self,
        db: AsyncSession,
        provider: str,
        oauth_id: str,
        email: str,
        username: str,
    ) -> Tuple[User, bool]:
        """Verify OAuth user and create if doesn't exist."""
        # Check if user exists by OAuth
        user = await self.user_repo.get_by_oauth(db, provider, oauth_id)
        if user:
            return user, False  # User exists
        
        # Check if email exists
        user = await self.user_repo.get_by_email(db, email)
        if user:
            # Link OAuth to existing user
            user.oauth_provider = provider  # type: ignore[assignment]
            user.oauth_id = oauth_id  # type: ignore[assignment]
            await db.commit()
            return user, False  # User exists, OAuth linked
        
        # Create new user
        user_data = UserRegister(
            email=email,
            username=username,
            password="",  # OAuth users don't need password
        )
        user = await self.user_repo.create(db, user_data)
        user.oauth_provider = provider  # type: ignore[assignment]
        user.oauth_id = oauth_id  # type: ignore[assignment]
        user.is_verified = True  # type: ignore[assignment]
        await db.commit()
        
        return user, True  # New user created
