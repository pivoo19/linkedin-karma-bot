"""Karma service for managing user karma and statistics.

This module provides the KarmaService class which handles all karma-related
operations including retrieving karma stats, post counts, and user status checks.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import User, Post, Reaction, UserKarma
from bot.database.repositories import UserKarmaRepository


class KarmaService:
    """Service for managing user karma and statistics.

    This service provides methods to retrieve and calculate karma-related
    metrics for users in the bot.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the KarmaService.

        Args:
            session: Async database session for executing queries
        """
        self.session = session

    async def get_weekly_karma(
        self,
        user_id: int,
        chat_id: int,
        period_days: int = 7
    ) -> int:
        """Get user's karma for a specific period in a chat.

        Karma is counted as the number of unique posts that the user
        supported (reacted to) in the specified chat within the period.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            period_days: Number of days to look back (default: 7)

        Returns:
            Number of unique posts the user supported in the period
        """
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)

        # Count unique posts that this user reacted to in this chat within the period
        query = (
            select(func.count(func.distinct(Reaction.post_id)))
            .join(Post, Reaction.post_id == Post.id)
            .where(
                Reaction.user_id == user_id,  # Reactions by this user
                Post.chat_id == chat_id,
                Reaction.created_at >= cutoff_date
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def get_total_karma(self, user_id: int, chat_id: Optional[int] = None) -> int:
        """Get user's total karma.

        If chat_id is provided, returns karma for that chat; otherwise falls back
        to the user's global karma_total.

        Args:
            user_id: Telegram user ID
            chat_id: Optional Telegram chat ID

        Returns:
            Total karma points
        """
        if chat_id is None:
            result = await self.session.execute(
                select(User.karma_total).where(User.telegram_id == user_id)
            )
            karma = result.scalar_one_or_none()
            return karma or 0

        karma_repo = UserKarmaRepository(self.session)
        return await karma_repo.get_total_karma(user_id, chat_id)

    async def get_weekly_posts_count(
        self,
        user_id: int,
        chat_id: int,
        period_days: int = 7
    ) -> int:
        """Get the number of posts a user made in a specific period.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            period_days: Number of days to look back (default: 7)

        Returns:
            Number of posts made in the specified period
        """
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)

        query = select(func.count(Post.id)).where(
            Post.author_id == user_id,
            Post.chat_id == chat_id,
            Post.created_at >= cutoff_date
        )

        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def is_newcomer(self, user_id: int) -> bool:
        """Check if a user is a newcomer (has never posted before).

        A newcomer is a user whose first_post_at field is NULL,
        indicating they haven't made their first post yet.

        Args:
            user_id: Telegram user ID

        Returns:
            True if the user is a newcomer, False otherwise
        """
        query = select(User.first_post_at).where(User.telegram_id == user_id)
        result = await self.session.execute(query)
        first_post_at = result.scalar_one_or_none()

        return first_post_at is None

    async def is_veteran(self, user_id: int, chat_id: Optional[int] = None, threshold: int = 30) -> bool:
        """Check if a user is a veteran (has total karma above threshold).

        Args:
            user_id: Telegram user ID
            chat_id: Optional Telegram chat ID
            threshold: Minimum karma points required to be a veteran (default: 30)

        Returns:
            True if the user's total karma is >= threshold, False otherwise
        """
        total_karma = await self.get_total_karma(user_id, chat_id)
        return total_karma >= threshold

    @staticmethod
    def karma_to_stars(karma: int) -> str:
        """Convert karma points to a star rating string.

        Args:
            karma: Karma points to convert

        Returns:
            Star rating as a string:
            - 0: "" (empty)
            - 1-2: "⭐"
            - 3-5: "⭐⭐"
            - 6-10: "⭐⭐⭐"
            - 11-20: "⭐⭐⭐⭐"
            - 21+: "⭐⭐⭐⭐⭐"

        Examples:
            >>> KarmaService.karma_to_stars(0)
            ''
            >>> KarmaService.karma_to_stars(1)
            '⭐'
            >>> KarmaService.karma_to_stars(5)
            '⭐⭐'
            >>> KarmaService.karma_to_stars(25)
            '⭐⭐⭐⭐⭐'
        """
        if karma == 0:
            return ""
        elif karma <= 2:
            return "⭐"
        elif karma <= 5:
            return "⭐⭐"
        elif karma <= 10:
            return "⭐⭐⭐"
        elif karma <= 20:
            return "⭐⭐⭐⭐"
        else:  # karma >= 21
            return "⭐⭐⭐⭐⭐"
