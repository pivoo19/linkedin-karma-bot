"""Tests for reaction handler behavior."""

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers import reactions as reactions_handler
from bot.models import Reaction, UserKarma


def make_reaction_update(
    *,
    user_id: int,
    chat_id: int,
    message_id: int,
    old_reaction: list[object],
    new_reaction: list[object],
    username: str = "reactor",
) -> SimpleNamespace:
    """Create a minimal reaction update object for handler tests."""
    return SimpleNamespace(
        user=SimpleNamespace(
            id=user_id,
            username=username,
            first_name="Reactor",
            last_name=None,
        ),
        chat=SimpleNamespace(id=chat_id),
        message_id=message_id,
        old_reaction=old_reaction,
        new_reaction=new_reaction,
    )


@pytest.fixture
def patch_reaction_session(monkeypatch, async_session: AsyncSession):
    """Patch handler session provider to use the test session."""

    @asynccontextmanager
    async def _get_session():
        yield async_session

    monkeypatch.setattr(reactions_handler, "get_session", _get_session)
    return async_session


async def test_reaction_add_increments_karma(
    patch_reaction_session: AsyncSession,
    sample_post,
):
    """No reaction -> reaction should create support and increment karma."""
    session = patch_reaction_session

    update = make_reaction_update(
        user_id=987654321,
        chat_id=sample_post.chat_id,
        message_id=sample_post.message_id,
        old_reaction=[],
        new_reaction=["👍"],
    )

    await reactions_handler.handle_reaction(update)

    reaction_result = await session.execute(
        select(Reaction).where(
            Reaction.post_id == sample_post.id,
            Reaction.user_id == 987654321,
        )
    )
    assert reaction_result.scalar_one_or_none() is not None

    karma_result = await session.execute(
        select(UserKarma).where(
            UserKarma.user_id == 987654321,
            UserKarma.chat_id == sample_post.chat_id,
        )
    )
    user_karma = karma_result.scalar_one_or_none()
    assert user_karma is not None
    assert user_karma.karma_total == 1


async def test_reaction_change_emoji_does_not_change_karma(
    patch_reaction_session: AsyncSession,
    sample_post,
):
    """One emoji -> another emoji should keep support state unchanged."""
    session = patch_reaction_session
    session.add(Reaction(post_id=sample_post.id, user_id=987654321))
    session.add(
        UserKarma(user_id=987654321, chat_id=sample_post.chat_id, karma_total=1)
    )
    await session.commit()

    update = make_reaction_update(
        user_id=987654321,
        chat_id=sample_post.chat_id,
        message_id=sample_post.message_id,
        old_reaction=["👍"],
        new_reaction=["🔥"],
    )

    await reactions_handler.handle_reaction(update)

    reaction_count_result = await session.execute(
        select(func.count(Reaction.id)).where(
            Reaction.post_id == sample_post.id,
            Reaction.user_id == 987654321,
        )
    )
    assert reaction_count_result.scalar_one() == 1

    karma_result = await session.execute(
        select(UserKarma).where(
            UserKarma.user_id == 987654321,
            UserKarma.chat_id == sample_post.chat_id,
        )
    )
    assert karma_result.scalar_one().karma_total == 1


async def test_reaction_remove_one_of_many_does_not_change_karma(
    patch_reaction_session: AsyncSession,
    sample_post,
):
    """Multiple emojis -> one emoji should keep support state unchanged."""
    session = patch_reaction_session
    session.add(Reaction(post_id=sample_post.id, user_id=987654321))
    session.add(
        UserKarma(user_id=987654321, chat_id=sample_post.chat_id, karma_total=1)
    )
    await session.commit()

    update = make_reaction_update(
        user_id=987654321,
        chat_id=sample_post.chat_id,
        message_id=sample_post.message_id,
        old_reaction=["👍", "🔥"],
        new_reaction=["🔥"],
    )

    await reactions_handler.handle_reaction(update)

    reaction_count_result = await session.execute(
        select(func.count(Reaction.id)).where(
            Reaction.post_id == sample_post.id,
            Reaction.user_id == 987654321,
        )
    )
    assert reaction_count_result.scalar_one() == 1

    karma_result = await session.execute(
        select(UserKarma).where(
            UserKarma.user_id == 987654321,
            UserKarma.chat_id == sample_post.chat_id,
        )
    )
    assert karma_result.scalar_one().karma_total == 1


async def test_reaction_remove_all_decrements_karma(
    patch_reaction_session: AsyncSession,
    sample_post,
):
    """Reaction -> no reactions should remove support and decrement karma."""
    session = patch_reaction_session
    session.add(Reaction(post_id=sample_post.id, user_id=987654321))
    session.add(
        UserKarma(user_id=987654321, chat_id=sample_post.chat_id, karma_total=1)
    )
    await session.commit()

    update = make_reaction_update(
        user_id=987654321,
        chat_id=sample_post.chat_id,
        message_id=sample_post.message_id,
        old_reaction=["👍"],
        new_reaction=[],
    )

    await reactions_handler.handle_reaction(update)

    reaction_result = await session.execute(
        select(Reaction).where(
            Reaction.post_id == sample_post.id,
            Reaction.user_id == 987654321,
        )
    )
    assert reaction_result.scalar_one_or_none() is None

    karma_result = await session.execute(
        select(UserKarma).where(
            UserKarma.user_id == 987654321,
            UserKarma.chat_id == sample_post.chat_id,
        )
    )
    assert karma_result.scalar_one().karma_total == 0


async def test_self_reaction_is_ignored(
    patch_reaction_session: AsyncSession,
    sample_post,
):
    """Self-reactions should not create support or karma records."""
    session = patch_reaction_session

    update = make_reaction_update(
        user_id=sample_post.author_id,
        chat_id=sample_post.chat_id,
        message_id=sample_post.message_id,
        old_reaction=[],
        new_reaction=["👍"],
    )

    await reactions_handler.handle_reaction(update)

    reaction_result = await session.execute(
        select(Reaction).where(
            Reaction.post_id == sample_post.id,
            Reaction.user_id == sample_post.author_id,
        )
    )
    assert reaction_result.scalar_one_or_none() is None

    karma_result = await session.execute(
        select(UserKarma).where(
            UserKarma.user_id == sample_post.author_id,
            UserKarma.chat_id == sample_post.chat_id,
        )
    )
    assert karma_result.scalar_one_or_none() is None
