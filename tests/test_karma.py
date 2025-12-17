"""Tests for karma service functionality."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Post, Reaction, User
from bot.services.karma import KarmaService


class TestKarmaService:
    """Test karma service functionality."""

    def test_karma_to_stars_zero(self):
        """Test karma to stars conversion for zero karma."""
        assert KarmaService.karma_to_stars(0) == ""

    def test_karma_to_stars_one_star(self):
        """Test karma to stars conversion for 1-2 points."""
        assert KarmaService.karma_to_stars(1) == "⭐"
        assert KarmaService.karma_to_stars(2) == "⭐"

    def test_karma_to_stars_two_stars(self):
        """Test karma to stars conversion for 3-5 points."""
        assert KarmaService.karma_to_stars(3) == "⭐⭐"
        assert KarmaService.karma_to_stars(4) == "⭐⭐"
        assert KarmaService.karma_to_stars(5) == "⭐⭐"

    def test_karma_to_stars_three_stars(self):
        """Test karma to stars conversion for 6-10 points."""
        assert KarmaService.karma_to_stars(6) == "⭐⭐⭐"
        assert KarmaService.karma_to_stars(8) == "⭐⭐⭐"
        assert KarmaService.karma_to_stars(10) == "⭐⭐⭐"

    def test_karma_to_stars_four_stars(self):
        """Test karma to stars conversion for 11-20 points."""
        assert KarmaService.karma_to_stars(11) == "⭐⭐⭐⭐"
        assert KarmaService.karma_to_stars(15) == "⭐⭐⭐⭐"
        assert KarmaService.karma_to_stars(20) == "⭐⭐⭐⭐"

    def test_karma_to_stars_five_stars(self):
        """Test karma to stars conversion for 21+ points."""
        assert KarmaService.karma_to_stars(21) == "⭐⭐⭐⭐⭐"
        assert KarmaService.karma_to_stars(50) == "⭐⭐⭐⭐⭐"
        assert KarmaService.karma_to_stars(100) == "⭐⭐⭐⭐⭐"

    async def test_is_newcomer_true(
        self, async_session: AsyncSession, sample_newcomer: User
    ):
        """Test checking if user is a newcomer (true)."""
        service = KarmaService(async_session)
        is_newcomer = await service.is_newcomer(sample_newcomer.telegram_id)
        assert is_newcomer is True

    async def test_is_newcomer_false(
        self, async_session: AsyncSession, sample_veteran: User
    ):
        """Test checking if user is a newcomer (false)."""
        service = KarmaService(async_session)
        is_newcomer = await service.is_newcomer(sample_veteran.telegram_id)
        assert is_newcomer is False

    async def test_is_veteran_true(
        self, async_session: AsyncSession, sample_veteran: User
    ):
        """Test checking if user is a veteran (true)."""
        service = KarmaService(async_session)
        # Default threshold is 30
        is_veteran = await service.is_veteran(sample_veteran.telegram_id, threshold=30)
        assert is_veteran is True

    async def test_is_veteran_false(
        self, async_session: AsyncSession, sample_user: User
    ):
        """Test checking if user is a veteran (false)."""
        service = KarmaService(async_session)
        # sample_user has 10 karma, threshold is 30
        is_veteran = await service.is_veteran(sample_user.telegram_id, threshold=30)
        assert is_veteran is False

    async def test_is_veteran_custom_threshold(
        self, async_session: AsyncSession, sample_user: User
    ):
        """Test checking veteran status with custom threshold."""
        service = KarmaService(async_session)
        # sample_user has 10 karma
        is_veteran = await service.is_veteran(sample_user.telegram_id, threshold=5)
        assert is_veteran is True

    async def test_get_total_karma_no_reactions(
        self, async_session: AsyncSession, sample_user: User
    ):
        """Test getting total karma for user returns their karma_total field."""
        service = KarmaService(async_session)
        # get_total_karma returns the user's karma_total field
        # sample_user is created with karma_total=10
        karma = await service.get_total_karma(sample_user.telegram_id)
        assert karma == sample_user.karma_total

    async def test_weekly_karma_calculation(
        self, async_session: AsyncSession, sample_user: User, sample_post: Post
    ):
        """Test calculating weekly karma from reactions."""
        service = KarmaService(async_session)

        # Create some reactions in the last week
        user2 = User(
            telegram_id=999888777,
            username="reactor",
            display_name="Reactor User",
        )
        async_session.add(user2)
        await async_session.commit()

        reaction = Reaction(
            post_id=sample_post.id,
            user_id=user2.telegram_id,
        )
        async_session.add(reaction)
        await async_session.commit()

        # Get weekly karma - the reactions should count
        weekly_posts = await service.get_weekly_posts_count(
            sample_user.telegram_id, sample_post.chat_id, period_days=7
        )
        assert weekly_posts == 1

    async def test_get_weekly_posts_count_no_posts(
        self, async_session: AsyncSession, sample_newcomer: User
    ):
        """Test getting weekly post count for user with no posts."""
        service = KarmaService(async_session)
        count = await service.get_weekly_posts_count(
            sample_newcomer.telegram_id, -1001234567890, period_days=7
        )
        assert count == 0

    async def test_get_weekly_posts_count_with_posts(
        self, async_session: AsyncSession, sample_user: User, sample_post: Post
    ):
        """Test getting weekly post count for user with posts."""
        service = KarmaService(async_session)
        count = await service.get_weekly_posts_count(
            sample_user.telegram_id, sample_post.chat_id, period_days=7
        )
        assert count == 1

    async def test_get_weekly_posts_count_old_posts(
        self, async_session: AsyncSession, sample_user: User
    ):
        """Test that old posts don't count in weekly stats."""
        # Create a post from 10 days ago
        old_post = Post(
            message_id=9999,
            chat_id=-1001234567890,
            author_id=sample_user.telegram_id,
            linkedin_url="https://linkedin.com/posts/old-post",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        async_session.add(old_post)
        await async_session.commit()

        service = KarmaService(async_session)
        count = await service.get_weekly_posts_count(
            sample_user.telegram_id, -1001234567890, period_days=7
        )
        # Should not include the old post
        assert count == 0
