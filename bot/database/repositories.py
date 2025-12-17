"""
Repository classes for database operations.

Each repository provides high-level async methods for working with specific models.
"""
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import select, func, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import User, Post, Reaction, GroupSettings, UserKarma


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> tuple[User, bool]:
        """
        Get an existing user or create a new one.

        Args:
            telegram_id: Telegram user ID
            username: Telegram username (optional)
            display_name: Display name (optional)

        Returns:
            Tuple of (User instance, created flag)
            created=True if user was just created, False if existing
        """
        # Try to get existing user
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is not None:
            # Update username and display_name if provided
            if username is not None and user.username != username:
                user.username = username
            if display_name is not None and user.display_name != display_name:
                user.display_name = display_name
            await self.session.commit()
            return user, False

        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=username,
            display_name=display_name,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user, True

    async def get_by_id(self, telegram_id: int) -> Optional[User]:
        """
        Get a user by their Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def update_karma_total(self, telegram_id: int, karma_delta: int) -> Optional[User]:
        """
        Update a user's total karma by adding a delta.

        Args:
            telegram_id: Telegram user ID
            karma_delta: Amount to add to karma (can be negative)

        Returns:
            Updated User instance or None if user not found
        """
        result = await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(karma_total=User.karma_total + karma_delta)
            .returning(User)
        )
        user = result.scalar_one_or_none()

        if user is not None:
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def set_first_post_time(self, telegram_id: int, post_time: datetime) -> Optional[User]:
        """
        Set the first_post_at timestamp for a user.

        Args:
            telegram_id: Telegram user ID
            post_time: Time of first post

        Returns:
            Updated User instance or None if user not found
        """
        result = await self.session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .where(User.first_post_at.is_(None))  # Only update if not set
            .values(first_post_at=post_time)
            .returning(User)
        )
        user = result.scalar_one_or_none()

        if user is not None:
            await self.session.commit()
            await self.session.refresh(user)

        return user


class PostRepository:
    """Repository for Post model operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def create(
        self,
        message_id: int,
        chat_id: int,
        author_id: int,
        linkedin_url: str,
    ) -> Post:
        """
        Create a new post.

        Args:
            message_id: Telegram message ID
            chat_id: Telegram chat ID
            author_id: Telegram user ID of the author
            linkedin_url: LinkedIn URL that was shared

        Returns:
            Created Post instance
        """
        post = Post(
            message_id=message_id,
            chat_id=chat_id,
            author_id=author_id,
            linkedin_url=linkedin_url,
        )
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)

        return post

    async def get_by_message(self, chat_id: int, message_id: int) -> Optional[Post]:
        """
        Get a post by its chat and message IDs.

        Args:
            chat_id: Telegram chat ID
            message_id: Telegram message ID

        Returns:
            Post instance or None if not found
        """
        result = await self.session.execute(
            select(Post).where(
                and_(
                    Post.chat_id == chat_id,
                    Post.message_id == message_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, post_id: int) -> Optional[Post]:
        """
        Get a post by its ID.

        Args:
            post_id: Post ID

        Returns:
            Post instance or None if not found
        """
        result = await self.session.execute(
            select(Post).where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    async def get_user_posts_in_period(
        self,
        user_id: int,
        days: int,
        chat_id: Optional[int] = None,
    ) -> List[Post]:
        """
        Get all posts by a user within a time period.

        Args:
            user_id: Telegram user ID
            days: Number of days to look back
            chat_id: Optional chat ID to filter by

        Returns:
            List of Post instances
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        query = select(Post).where(
            and_(
                Post.author_id == user_id,
                Post.created_at >= cutoff_time,
            )
        )

        if chat_id is not None:
            query = query.where(Post.chat_id == chat_id)

        result = await self.session.execute(query.order_by(Post.created_at.desc()))
        return list(result.scalars().all())

    async def count_user_posts_in_period(
        self,
        user_id: int,
        days: int,
        chat_id: Optional[int] = None,
    ) -> int:
        """
        Count posts by a user within a time period.

        Args:
            user_id: Telegram user ID
            days: Number of days to look back
            chat_id: Optional chat ID to filter by

        Returns:
            Number of posts
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        query = select(func.count(Post.id)).where(
            and_(
                Post.author_id == user_id,
                Post.created_at >= cutoff_time,
            )
        )

        if chat_id is not None:
            query = query.where(Post.chat_id == chat_id)

        result = await self.session.execute(query)
        return result.scalar_one()


class ReactionRepository:
    """Repository for Reaction model operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def add_reaction(self, post_id: int, user_id: int) -> Optional[Reaction]:
        """
        Add a reaction to a post.

        Args:
            post_id: Post ID
            user_id: Telegram user ID

        Returns:
            Created Reaction instance, or None if it already exists
        """
        # Check if reaction already exists
        result = await self.session.execute(
            select(Reaction).where(
                and_(
                    Reaction.post_id == post_id,
                    Reaction.user_id == user_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            return None  # Reaction already exists

        # Create new reaction
        reaction = Reaction(
            post_id=post_id,
            user_id=user_id,
        )
        self.session.add(reaction)
        await self.session.commit()
        await self.session.refresh(reaction)

        return reaction

    async def remove_reaction(self, post_id: int, user_id: int) -> bool:
        """
        Remove a reaction from a post.

        Args:
            post_id: Post ID
            user_id: Telegram user ID

        Returns:
            True if reaction was removed, False if it didn't exist
        """
        result = await self.session.execute(
            delete(Reaction).where(
                and_(
                    Reaction.post_id == post_id,
                    Reaction.user_id == user_id,
                )
            ).returning(Reaction.id)
        )
        deleted_id = result.scalar_one_or_none()

        if deleted_id is not None:
            await self.session.commit()
            return True

        return False

    async def get_reaction(self, post_id: int, user_id: int) -> Optional[Reaction]:
        """
        Get a specific reaction.

        Args:
            post_id: Post ID
            user_id: Telegram user ID

        Returns:
            Reaction instance or None if not found
        """
        result = await self.session.execute(
            select(Reaction).where(
                and_(
                    Reaction.post_id == post_id,
                    Reaction.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_post_reactions(self, post_id: int) -> List[Reaction]:
        """
        Get all reactions for a post.

        Args:
            post_id: Post ID

        Returns:
            List of Reaction instances
        """
        result = await self.session.execute(
            select(Reaction)
            .where(Reaction.post_id == post_id)
            .order_by(Reaction.created_at)
        )
        return list(result.scalars().all())

    async def get_user_reactions_in_period(
        self,
        user_id: int,
        days: int,
    ) -> List[Reaction]:
        """
        Get all reactions by a user within a time period.

        Args:
            user_id: Telegram user ID
            days: Number of days to look back

        Returns:
            List of Reaction instances
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(Reaction)
            .where(
                and_(
                    Reaction.user_id == user_id,
                    Reaction.created_at >= cutoff_time,
                )
            )
            .order_by(Reaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_user_reactions_in_period(
        self,
        user_id: int,
        days: int,
    ) -> int:
        """
        Count reactions by a user within a time period.

        Args:
            user_id: Telegram user ID
            days: Number of days to look back

        Returns:
            Number of reactions
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(func.count(Reaction.id)).where(
                and_(
                    Reaction.user_id == user_id,
                    Reaction.created_at >= cutoff_time,
                )
            )
        )
        return result.scalar_one()


class SettingsRepository:
    """Repository for GroupSettings model operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_or_create(self, chat_id: int) -> tuple[GroupSettings, bool]:
        """
        Get existing group settings or create with defaults.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Tuple of (GroupSettings instance, created flag)
            created=True if settings were just created, False if existing
        """
        # Try to get existing settings
        result = await self.session.execute(
            select(GroupSettings).where(GroupSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()

        if settings is not None:
            return settings, False

        # Create new settings with defaults
        settings = GroupSettings(chat_id=chat_id)
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)

        return settings, True

    async def get(self, chat_id: int) -> Optional[GroupSettings]:
        """
        Get group settings.

        Args:
            chat_id: Telegram chat ID

        Returns:
            GroupSettings instance or None if not found
        """
        result = await self.session.execute(
            select(GroupSettings).where(GroupSettings.chat_id == chat_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        chat_id: int,
        language: Optional[str] = None,
        karma_period_days: Optional[int] = None,
        veteran_threshold: Optional[int] = None,
        post_cost: Optional[int] = None,
    ) -> Optional[GroupSettings]:
        """
        Update group settings.

        Args:
            chat_id: Telegram chat ID
            language: Language code (optional)
            karma_period_days: Karma period in days (optional)
            veteran_threshold: Veteran threshold in days (optional)
            post_cost: Karma cost to post (optional)

        Returns:
            Updated GroupSettings instance or None if not found
        """
        # Build update values dict
        values = {}
        if language is not None:
            values["language"] = language
        if karma_period_days is not None:
            values["karma_period_days"] = karma_period_days
        if veteran_threshold is not None:
            values["veteran_threshold"] = veteran_threshold
        if post_cost is not None:
            values["post_cost"] = post_cost

        if not values:
            # Nothing to update, just return existing settings
            return await self.get(chat_id)

        result = await self.session.execute(
            update(GroupSettings)
            .where(GroupSettings.chat_id == chat_id)
            .values(**values)
            .returning(GroupSettings)
        )
        settings = result.scalar_one_or_none()

        if settings is not None:
            await self.session.commit()
            await self.session.refresh(settings)

        return settings


class UserKarmaRepository:
    """Repository for UserKarma model operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_or_create(
        self,
        user_id: int,
        chat_id: int,
    ) -> tuple[UserKarma, bool]:
        """
        Get existing user karma record or create a new one.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID

        Returns:
            Tuple of (UserKarma instance, created flag)
            created=True if record was just created, False if existing
        """
        # Try to get existing record
        result = await self.session.execute(
            select(UserKarma).where(
                and_(
                    UserKarma.user_id == user_id,
                    UserKarma.chat_id == chat_id
                )
            )
        )
        user_karma = result.scalar_one_or_none()

        if user_karma is not None:
            return user_karma, False

        # Create new record
        user_karma = UserKarma(
            user_id=user_id,
            chat_id=chat_id,
            karma_total=0
        )
        self.session.add(user_karma)
        await self.session.commit()
        await self.session.refresh(user_karma)

        return user_karma, True

    async def get(
        self,
        user_id: int,
        chat_id: int,
    ) -> Optional[UserKarma]:
        """
        Get user karma record.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID

        Returns:
            UserKarma instance or None if not found
        """
        result = await self.session.execute(
            select(UserKarma).where(
                and_(
                    UserKarma.user_id == user_id,
                    UserKarma.chat_id == chat_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_karma_total(
        self,
        user_id: int,
        chat_id: int,
        karma_delta: int
    ) -> Optional[UserKarma]:
        """
        Update user's karma in a chat by adding a delta.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            karma_delta: Amount to add to karma (can be negative)

        Returns:
            Updated UserKarma instance or None if not found
        """
        # Get or create the record first
        user_karma, _ = await self.get_or_create(user_id, chat_id)

        # Update karma
        result = await self.session.execute(
            update(UserKarma)
            .where(
                and_(
                    UserKarma.user_id == user_id,
                    UserKarma.chat_id == chat_id
                )
            )
            .values(karma_total=UserKarma.karma_total + karma_delta)
            .returning(UserKarma)
        )
        user_karma = result.scalar_one_or_none()

        if user_karma is not None:
            await self.session.commit()
            await self.session.refresh(user_karma)

        return user_karma

    async def get_total_karma(
        self,
        user_id: int,
        chat_id: int
    ) -> int:
        """
        Get user's total karma in a chat.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID

        Returns:
            Total karma points in this chat, or 0 if record doesn't exist
        """
        user_karma = await self.get(user_id, chat_id)
        return user_karma.karma_total if user_karma else 0

    async def reset_karma(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserKarma]:
        """
        Reset user's karma to zero in a chat.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID

        Returns:
            Updated UserKarma instance or None if not found
        """
        result = await self.session.execute(
            update(UserKarma)
            .where(
                and_(
                    UserKarma.user_id == user_id,
                    UserKarma.chat_id == chat_id
                )
            )
            .values(karma_total=0)
            .returning(UserKarma)
        )
        user_karma = result.scalar_one_or_none()

        if user_karma is not None:
            await self.session.commit()
            await self.session.refresh(user_karma)

        return user_karma
