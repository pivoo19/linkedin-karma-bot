"""Pytest configuration and fixtures for LinkedIn Karma Bot tests."""

from datetime import datetime
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.models import Base, GroupSettings, Post, Reaction, User


@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def sample_user(async_session: AsyncSession) -> User:
    """Create a sample user for testing."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        display_name="Test User",
        karma_total=10,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def sample_user_2(async_session: AsyncSession) -> User:
    """Create a second sample user for testing."""
    user = User(
        telegram_id=987654321,
        username="testuser2",
        display_name="Test User 2",
        karma_total=5,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def sample_newcomer(async_session: AsyncSession) -> User:
    """Create a newcomer user (no first_post_at) for testing."""
    user = User(
        telegram_id=111222333,
        username="newcomer",
        display_name="New User",
        karma_total=0,
        first_post_at=None,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def sample_veteran(async_session: AsyncSession) -> User:
    """Create a veteran user (high karma) for testing."""
    user = User(
        telegram_id=444555666,
        username="veteran",
        display_name="Veteran User",
        karma_total=50,
        first_post_at=datetime(2023, 1, 1, 12, 0, 0),
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def sample_post(async_session: AsyncSession, sample_user: User) -> Post:
    """Create a sample post for testing."""
    post = Post(
        message_id=1001,
        chat_id=-1001234567890,
        author_id=sample_user.telegram_id,
        linkedin_url="https://linkedin.com/posts/testuser-123_post",
    )
    async_session.add(post)
    await async_session.commit()
    await async_session.refresh(post)
    return post


@pytest.fixture
async def sample_post_2(async_session: AsyncSession, sample_user_2: User) -> Post:
    """Create a second sample post for testing."""
    post = Post(
        message_id=1002,
        chat_id=-1001234567890,
        author_id=sample_user_2.telegram_id,
        linkedin_url="https://linkedin.com/posts/testuser2-456_another-post",
    )
    async_session.add(post)
    await async_session.commit()
    await async_session.refresh(post)
    return post


@pytest.fixture
async def sample_reaction(
    async_session: AsyncSession, sample_user_2: User, sample_post: Post
) -> Reaction:
    """Create a sample reaction for testing."""
    reaction = Reaction(
        post_id=sample_post.id,
        user_id=sample_user_2.telegram_id,
    )
    async_session.add(reaction)
    await async_session.commit()
    await async_session.refresh(reaction)
    return reaction


@pytest.fixture
async def sample_settings(async_session: AsyncSession) -> GroupSettings:
    """Create sample group settings for testing."""
    settings = GroupSettings(
        chat_id=-1001234567890,
        language="en",
        karma_period_days=7,
        veteran_threshold=30,
        post_cost=0,
    )
    async_session.add(settings)
    await async_session.commit()
    await async_session.refresh(settings)
    return settings
