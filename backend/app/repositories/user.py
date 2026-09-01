from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.user import User, UserSettings, Session as UserSession, APIKey
from app.schemas.auth import UserRegister
from pydantic import BaseModel


class UserUpdate(BaseModel):
    """User update schema (placeholder)."""
    pass


class UserRepository(BaseRepository[User, UserRegister, UserUpdate]):
    """Repository for User model operations."""

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_username(
        self,
        db: AsyncSession,
        username: str,
    ) -> Optional[User]:
        """Get user by username."""
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_oauth(
        self,
        db: AsyncSession,
        provider: str,
        oauth_id: str,
    ) -> Optional[User]:
        """Get user by OAuth provider and ID."""
        query = select(User).where(
            and_(
                User.oauth_provider == provider,
                User.oauth_id == oauth_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_or_create_by_oauth(
        self,
        db: AsyncSession,
        user_data: UserRegister,
        provider: str,
        oauth_id: str,
    ) -> User:
        """Get user by OAuth provider and ID, or create a new one."""
        user = await self.get_by_oauth(db, provider, oauth_id)
        
        if not user:
            user = await self.create(db, user_data)
            user.oauth_provider = provider  # type: ignore[assignment]
            user.oauth_id = oauth_id  # type: ignore[assignment]
            user.is_verified = True  # type: ignore[assignment]
            await db.commit()
        
        return user

    async def get_with_settings(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        """Get user with settings loaded."""
        query = select(User).options(
            selectinload(User.settings)
        ).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_active_sessions(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> List[UserSession]:
        """Get all active sessions for a user."""
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > select(func.now())
            )
        ).order_by(UserSession.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def invalidate_all_sessions(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> int:
        """Invalidate all sessions for a user."""
        from sqlalchemy import update
        
        query = update(UserSession).where(
            UserSession.user_id == user_id
        ).values(is_active=False)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount  # type: ignore[no-any-return]

    async def increment_failed_login(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        """Increment failed login attempts."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.failed_login_attempts += 1  # type: ignore[assignment]
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                from datetime import datetime, timedelta
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)  # type: ignore[assignment]
            
            await db.commit()
            await db.refresh(user)
        
        return user if user else None

    async def reset_failed_login(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        """Reset failed login attempts."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.failed_login_attempts = 0  # type: ignore[assignment]
            user.locked_until = None  # type: ignore[assignment]
            await db.commit()
            await db.refresh(user)
        
        return user if user else None


class UserSettingsRepository(BaseRepository[UserSettings, BaseModel, BaseModel]):
    """Repository for UserSettings model operations."""

    async def get_by_user_id(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[UserSettings]:
        """Get settings by user ID."""
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_or_create(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> UserSettings:
        """Get existing settings or create default."""
        settings = await self.get_by_user_id(db, user_id)
        
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        
        return settings


class APIKeyRepository(BaseRepository[APIKey, BaseModel, BaseModel]):
    """Repository for APIKey model operations."""

    async def get_by_key(
        self,
        db: AsyncSession,
        key: str,
    ) -> Optional[APIKey]:
        """Get API key by key string."""
        query = select(APIKey).where(
            and_(
                APIKey.key == key,
                APIKey.is_active == True,
                APIKey.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[APIKey]:
        """Get API keys for a user."""
        query = select(APIKey).where(
            and_(
                APIKey.user_id == user_id,
                APIKey.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).order_by(APIKey.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def revoke(
        self,
        db: AsyncSession,
        key_id: int,
        user_id: int,
    ) -> bool:
        """Revoke an API key."""
        from datetime import datetime
        
        query = select(APIKey).where(
            and_(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        )
        result = await db.execute(query)
        api_key = result.scalar_one_or_none()
        
        if api_key:
            api_key.is_active = False  # type: ignore[assignment]
            api_key.deleted_at = datetime.utcnow()  # type: ignore[assignment]
            await db.commit()
            return True
        
        return False


class SessionRepository(BaseRepository[UserSession, BaseModel, BaseModel]):
    """Repository for Session model operations."""

    async def get_by_token(
        self,
        db: AsyncSession,
        token: str,
    ) -> Optional[UserSession]:
        """Get session by access token."""
        from datetime import datetime
        
        query = select(UserSession).where(
            and_(
                UserSession.token == token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> Optional[UserSession]:
        """Get session by refresh token."""
        from datetime import datetime
        
        query = select(UserSession).where(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def cleanup_expired(
        self,
        db: AsyncSession,
    ) -> int:
        """Clean up expired sessions."""
        from datetime import datetime
        from sqlalchemy import delete
        
        query = delete(UserSession).where(
            UserSession.expires_at < datetime.utcnow()
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount  # type: ignore[no-any-return]
