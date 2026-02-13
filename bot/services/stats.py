"""Statistics service for group-level analytics.

This module provides the StatsService class which handles group statistics
including user counts, post counts, and reaction metrics.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Post, Reaction
from bot.services.karma import KarmaService


class StatsService:
    """Service for managing group statistics.

    This service provides methods to retrieve and calculate statistics
    for Telegram groups using the bot.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the StatsService.

        Args:
            session: Async database session for executing queries
        """
        self.session = session

    async def _count_first_hour_reactions(
        self,
        chat_id: int,
        cutoff_date: datetime | None = None
    ) -> int:
        """Count reactions on chat posts that were made in first hour."""
        query = (
            select(Reaction.created_at, Post.created_at)
            .join(Post, Reaction.post_id == Post.id)
            .where(Post.chat_id == chat_id)
        )
        if cutoff_date is not None:
            query = query.where(Reaction.created_at >= cutoff_date)

        result = await self.session.execute(query)
        rows = result.all()

        return sum(
            1 for reaction_time, post_time in rows
            if KarmaService.is_within_first_hour(reaction_time, post_time)
        )

    async def get_group_stats(self, chat_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific group.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Dictionary containing:
            - total_users: Total number of unique users (who posted or reacted)
            - total_posts: Total number of posts in the group
            - total_reactions: Total number of reactions given
            - weekly_posts: Number of posts in the last 7 days
            - weekly_reactions: Number of reactions in the last 7 days

        Example:
            >>> stats = await stats_service.get_group_stats(chat_id=-123456)
            >>> print(f"Total users: {stats['total_users']}")
            Total users: 42
        """
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        # Total unique users (who posted OR reacted) in this chat
        # Get all user IDs from posts
        post_users_query = select(Post.author_id).where(
            Post.chat_id == chat_id
        ).distinct()
        
        # Get all user IDs from reactions (through posts in this chat)
        reaction_users_query = (
            select(Reaction.user_id)
            .join(Post, Reaction.post_id == Post.id)
            .where(Post.chat_id == chat_id)
            .distinct()
        )
        
        # Execute both queries and combine results
        post_users_result = await self.session.execute(post_users_query)
        post_user_ids = set(post_users_result.scalars().all())
        
        reaction_users_result = await self.session.execute(reaction_users_query)
        reaction_user_ids = set(reaction_users_result.scalars().all())
        
        # Count unique users (union of both sets)
        total_users = len(post_user_ids | reaction_user_ids)

        # Total posts in the group
        total_posts_query = select(func.count(Post.id)).where(
            Post.chat_id == chat_id
        )
        total_posts_result = await self.session.execute(total_posts_query)
        total_posts = total_posts_result.scalar_one() or 0

        # Total reactions in the group (reactions on posts in this chat)
        total_reactions_query = (
            select(func.count(Reaction.id))
            .join(Post, Reaction.post_id == Post.id)
            .where(Post.chat_id == chat_id)
        )
        total_reactions_result = await self.session.execute(total_reactions_query)
        total_reactions = total_reactions_result.scalar_one() or 0

        # Weekly posts
        weekly_posts_query = select(func.count(Post.id)).where(
            Post.chat_id == chat_id,
            Post.created_at >= cutoff_date
        )
        weekly_posts_result = await self.session.execute(weekly_posts_query)
        weekly_posts = weekly_posts_result.scalar_one() or 0

        # Weekly reactions (reactions on posts in this chat within the period)
        weekly_reactions_query = (
            select(func.count(Reaction.id))
            .join(Post, Reaction.post_id == Post.id)
            .where(
                Post.chat_id == chat_id,
                Reaction.created_at >= cutoff_date
            )
        )
        weekly_reactions_result = await self.session.execute(weekly_reactions_query)
        weekly_reactions = weekly_reactions_result.scalar_one() or 0

        total_first_hour_reactions = await self._count_first_hour_reactions(chat_id)
        weekly_first_hour_reactions = await self._count_first_hour_reactions(
            chat_id, cutoff_date=cutoff_date
        )

        return {
            "total_users": total_users,
            "total_posts": total_posts,
            "total_reactions": total_reactions,
            "total_first_hour_reactions": total_first_hour_reactions,
            "weekly_posts": weekly_posts,
            "weekly_reactions": weekly_reactions,
            "weekly_first_hour_reactions": weekly_first_hour_reactions,
        }
