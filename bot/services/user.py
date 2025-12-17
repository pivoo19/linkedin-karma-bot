"""User service for user-related database operations."""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import User, Post, GroupSettings


class UserService:
    """Service for user-related operations."""

    def __init__(self, session: AsyncSession):
        """Initialize user service.

        Args:
            session: Database session
        """
        self.session = session

    async def get_or_create_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Get existing user or create new one.

        Args:
            user_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name

        Returns:
            User object
        """
        # Build display name from first and last name
        display_name = None
        if first_name:
            display_name = first_name
            if last_name:
                display_name = f"{first_name} {last_name}"

        # Try to get existing user
        result = await self.session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update user info if changed
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if display_name and user.display_name != display_name:
                user.display_name = display_name
                updated = True

            if updated:
                await self.session.commit()
                await self.session.refresh(user)
        else:
            # Create new user - note: first_post_at will be NULL initially
            user = User(
                telegram_id=user_id,
                username=username,
                display_name=display_name,
                karma_total=0
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def create_post(
        self,
        user_id: int,
        message_id: int,
        chat_id: int,
        linkedin_url: str
    ) -> Post:
        """Create new post record.

        Args:
            user_id: User's Telegram ID
            message_id: Telegram message ID
            chat_id: Telegram chat ID
            linkedin_url: LinkedIn URL

        Returns:
            Created post
        """
        post = Post(
            author_id=user_id,
            message_id=message_id,
            chat_id=chat_id,
            linkedin_url=linkedin_url
        )
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: Telegram user ID

        Returns:
            User or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username (without @)

        Returns:
            User or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_post_by_message(
        self,
        chat_id: int,
        message_id: int
    ) -> Optional[Post]:
        """Get post by message ID.

        Args:
            chat_id: Telegram chat ID
            message_id: Telegram message ID

        Returns:
            Post or None if not found
        """
        result = await self.session.execute(
            select(Post).where(
                Post.chat_id == chat_id,
                Post.message_id == message_id
            )
        )
        return result.scalar_one_or_none()

    async def reset_user_karma(self, user: User) -> None:
        """Reset user's karma to zero.

        Args:
            user: User to reset
        """
        user.karma_total = 0
        await self.session.commit()

    async def get_or_create_settings(self, chat_id: int) -> GroupSettings:
        """Get or create group settings.

        Args:
            chat_id: Telegram chat ID

        Returns:
            GroupSettings object
        """
        result = await self.session.execute(
            select(GroupSettings).where(GroupSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = GroupSettings(chat_id=chat_id)
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)

        return settings

    async def update_settings(
        self,
        chat_id: int,
        **kwargs
    ) -> GroupSettings:
        """Update group settings.

        Args:
            chat_id: Telegram chat ID
            **kwargs: Settings to update

        Returns:
            Updated GroupSettings object
        """
        settings = await self.get_or_create_settings(chat_id)

        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        await self.session.commit()
        await self.session.refresh(settings)
        return settings
