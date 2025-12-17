"""Tests for database repositories."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import (
    PostRepository,
    ReactionRepository,
    SettingsRepository,
    UserRepository,
)
from bot.models import GroupSettings, Post, Reaction, User


class TestUserRepository:
    """Test UserRepository functionality."""

    async def test_user_get_or_create_new(self, async_session: AsyncSession):
        """Test creating a new user."""
        repo = UserRepository(async_session)
        user, created = await repo.get_or_create(
            telegram_id=555666777,
            username="newuser",
            display_name="New User",
        )

        assert created is True
        assert user.telegram_id == 555666777
        assert user.username == "newuser"
        assert user.display_name == "New User"
        assert user.karma_total == 0

    async def test_user_get_or_create_existing(
        self, async_session: AsyncSession, sample_user: User
    ):
        """Test getting an existing user."""
        repo = UserRepository(async_session)
        user, created = await repo.get_or_create(
            telegram_id=sample_user.telegram_id,
            username="updatedusername",
        )

        assert created is False
        assert user.telegram_id == sample_user.telegram_id
        # Username should be updated
        assert user.username == "updatedusername"

    async def test_user_get_by_id_exists(
        self, async_session: AsyncSession, sample_user: User
    ):
        """Test getting user by ID when user exists."""
        repo = UserRepository(async_session)
        user = await repo.get_by_id(sample_user.telegram_id)

        assert user is not None
        assert user.telegram_id == sample_user.telegram_id
        assert user.username == sample_user.username

    async def test_user_get_by_id_not_exists(self, async_session: AsyncSession):
        """Test getting user by ID when user doesn't exist."""
        repo = UserRepository(async_session)
        user = await repo.get_by_id(999999999)

        assert user is None

    async def test_user_update_karma_total(
        self, async_session: AsyncSession, sample_user: User
    ):
        """Test updating user's total karma."""
        repo = UserRepository(async_session)
        initial_karma = sample_user.karma_total

        updated_user = await repo.update_karma_total(sample_user.telegram_id, 5)

        assert updated_user is not None
        assert updated_user.karma_total == initial_karma + 5

    async def test_user_set_first_post_time(
        self, async_session: AsyncSession, sample_newcomer: User
    ):
        """Test setting first post time for newcomer."""
        repo = UserRepository(async_session)
        post_time = datetime.utcnow()

        updated_user = await repo.set_first_post_time(
            sample_newcomer.telegram_id, post_time
        )

        assert updated_user is not None
        assert updated_user.first_post_at is not None


class TestPostRepository:
    """Test PostRepository functionality."""

    async def test_post_create(self, async_session: AsyncSession, sample_user: User):
        """Test creating a new post."""
        repo = PostRepository(async_session)
        post = await repo.create(
            message_id=2001,
            chat_id=-1001234567890,
            author_id=sample_user.telegram_id,
            linkedin_url="https://linkedin.com/posts/test-new-post",
        )

        assert post.id is not None
        assert post.message_id == 2001
        assert post.chat_id == -1001234567890
        assert post.author_id == sample_user.telegram_id
        assert "linkedin.com" in post.linkedin_url

    async def test_post_get_by_message(
        self, async_session: AsyncSession, sample_post: Post
    ):
        """Test getting post by message ID and chat ID."""
        repo = PostRepository(async_session)
        post = await repo.get_by_message(sample_post.chat_id, sample_post.message_id)

        assert post is not None
        assert post.id == sample_post.id
        assert post.message_id == sample_post.message_id

    async def test_post_get_by_message_not_exists(self, async_session: AsyncSession):
        """Test getting non-existent post."""
        repo = PostRepository(async_session)
        post = await repo.get_by_message(-999, 9999)

        assert post is None

    async def test_post_get_by_id(
        self, async_session: AsyncSession, sample_post: Post
    ):
        """Test getting post by ID."""
        repo = PostRepository(async_session)
        post = await repo.get_by_id(sample_post.id)

        assert post is not None
        assert post.id == sample_post.id

    async def test_post_count_user_posts_in_period(
        self, async_session: AsyncSession, sample_user: User, sample_post: Post
    ):
        """Test counting user posts in a time period."""
        repo = PostRepository(async_session)

        # Create another recent post
        await repo.create(
            message_id=2002,
            chat_id=sample_post.chat_id,
            author_id=sample_user.telegram_id,
            linkedin_url="https://linkedin.com/posts/another-post",
        )

        count = await repo.count_user_posts_in_period(
            sample_user.telegram_id, days=7, chat_id=sample_post.chat_id
        )

        assert count == 2

    async def test_post_count_user_posts_old_excluded(
        self, async_session: AsyncSession, sample_user: User
    ):
        """Test that old posts are excluded from period count."""
        # Create an old post
        old_post = Post(
            message_id=9001,
            chat_id=-1001234567890,
            author_id=sample_user.telegram_id,
            linkedin_url="https://linkedin.com/posts/old-post",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        async_session.add(old_post)
        await async_session.commit()

        repo = PostRepository(async_session)
        count = await repo.count_user_posts_in_period(
            sample_user.telegram_id, days=7, chat_id=-1001234567890
        )

        assert count == 0


class TestReactionRepository:
    """Test ReactionRepository functionality."""

    async def test_reaction_add(
        self, async_session: AsyncSession, sample_post: Post, sample_user_2: User
    ):
        """Test adding a reaction to a post."""
        repo = ReactionRepository(async_session)
        reaction = await repo.add_reaction(sample_post.id, sample_user_2.telegram_id)

        assert reaction is not None
        assert reaction.post_id == sample_post.id
        assert reaction.user_id == sample_user_2.telegram_id

    async def test_reaction_add_duplicate(
        self, async_session: AsyncSession, sample_post: Post, sample_user_2: User
    ):
        """Test that duplicate reactions are not allowed."""
        repo = ReactionRepository(async_session)

        # Add first reaction
        reaction1 = await repo.add_reaction(sample_post.id, sample_user_2.telegram_id)
        assert reaction1 is not None

        # Try to add duplicate
        reaction2 = await repo.add_reaction(sample_post.id, sample_user_2.telegram_id)
        assert reaction2 is None

    async def test_reaction_remove(
        self, async_session: AsyncSession, sample_reaction: Reaction
    ):
        """Test removing a reaction."""
        repo = ReactionRepository(async_session)
        removed = await repo.remove_reaction(
            sample_reaction.post_id, sample_reaction.user_id
        )

        assert removed is True

        # Verify it's gone
        reaction = await repo.get_reaction(
            sample_reaction.post_id, sample_reaction.user_id
        )
        assert reaction is None

    async def test_reaction_remove_nonexistent(
        self, async_session: AsyncSession, sample_post: Post
    ):
        """Test removing a non-existent reaction."""
        repo = ReactionRepository(async_session)
        removed = await repo.remove_reaction(sample_post.id, 999999999)

        assert removed is False

    async def test_reaction_get_post_reactions(
        self, async_session: AsyncSession, sample_post: Post, sample_reaction: Reaction
    ):
        """Test getting all reactions for a post."""
        repo = ReactionRepository(async_session)
        reactions = await repo.get_post_reactions(sample_post.id)

        assert len(reactions) >= 1
        assert any(r.id == sample_reaction.id for r in reactions)

    async def test_reaction_count_user_reactions_in_period(
        self, async_session: AsyncSession, sample_user: User, sample_post: Post
    ):
        """Test counting user reactions in a time period."""
        repo = ReactionRepository(async_session)

        # Add reactions
        await repo.add_reaction(sample_post.id, sample_user.telegram_id)

        count = await repo.count_user_reactions_in_period(
            sample_user.telegram_id, days=7
        )

        assert count >= 1


class TestSettingsRepository:
    """Test SettingsRepository functionality."""

    async def test_settings_get_or_create_new(self, async_session: AsyncSession):
        """Test creating new group settings."""
        repo = SettingsRepository(async_session)
        settings, created = await repo.get_or_create(chat_id=-9876543210)

        assert created is True
        assert settings.chat_id == -9876543210
        assert settings.language == "ru"  # default
        assert settings.karma_period_days == 7  # default
        assert settings.veteran_threshold == 30  # default
        assert settings.post_cost == 0  # default

    async def test_settings_get_or_create_existing(
        self, async_session: AsyncSession, sample_settings: GroupSettings
    ):
        """Test getting existing group settings."""
        repo = SettingsRepository(async_session)
        settings, created = await repo.get_or_create(sample_settings.chat_id)

        assert created is False
        assert settings.chat_id == sample_settings.chat_id
        assert settings.language == sample_settings.language

    async def test_settings_get(
        self, async_session: AsyncSession, sample_settings: GroupSettings
    ):
        """Test getting group settings."""
        repo = SettingsRepository(async_session)
        settings = await repo.get(sample_settings.chat_id)

        assert settings is not None
        assert settings.chat_id == sample_settings.chat_id

    async def test_settings_get_not_exists(self, async_session: AsyncSession):
        """Test getting non-existent settings."""
        repo = SettingsRepository(async_session)
        settings = await repo.get(-999999999)

        assert settings is None

    async def test_settings_update(
        self, async_session: AsyncSession, sample_settings: GroupSettings
    ):
        """Test updating group settings."""
        repo = SettingsRepository(async_session)
        updated_settings = await repo.update(
            sample_settings.chat_id,
            language="ru",
            karma_period_days=14,
            veteran_threshold=60,
            post_cost=5,
        )

        assert updated_settings is not None
        assert updated_settings.language == "ru"
        assert updated_settings.karma_period_days == 14
        assert updated_settings.veteran_threshold == 60
        assert updated_settings.post_cost == 5

    async def test_settings_update_partial(
        self, async_session: AsyncSession, sample_settings: GroupSettings
    ):
        """Test partially updating group settings."""
        repo = SettingsRepository(async_session)
        original_language = sample_settings.language

        updated_settings = await repo.update(
            sample_settings.chat_id, karma_period_days=10
        )

        assert updated_settings is not None
        assert updated_settings.language == original_language  # unchanged
        assert updated_settings.karma_period_days == 10  # updated
