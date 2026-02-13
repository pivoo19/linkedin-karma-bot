"""Tests for LinkedIn message handler output formatting."""

from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers import messages as messages_handler
from bot.i18n import t
from bot.models import GroupSettings, User, UserKarma


@pytest.fixture
def patch_messages_session(monkeypatch, async_session: AsyncSession):
    """Patch message handler session provider to use the test session."""

    @asynccontextmanager
    async def _get_session():
        yield async_session

    monkeypatch.setattr(messages_handler, "get_session", _get_session)
    return async_session


@pytest.fixture
def patch_notify_users(monkeypatch):
    """Avoid external notification side effects in handler tests."""
    notify_mock = AsyncMock()
    monkeypatch.setattr(messages_handler, "notify_users", notify_mock)
    return notify_mock


def make_message(
    *,
    user_id: int,
    username: str,
    message_id: int,
    chat_id: int = -1001234567890,
    text: str = "https://linkedin.com/posts/test-post",
):
    """Create a minimal message object for LinkedIn handler tests."""
    return SimpleNamespace(
        text=text,
        entities=None,
        message_id=message_id,
        chat=SimpleNamespace(id=chat_id, username=None),
        from_user=SimpleNamespace(
            id=user_id,
            username=username,
            first_name="Test",
            last_name=None,
        ),
        reply=AsyncMock(),
        bot=SimpleNamespace(),
    )


async def test_post_message_newcomer_includes_all_time_line_with_zero(
    patch_messages_session: AsyncSession,
    patch_notify_users,
):
    """Newcomer post response should include explicit all-time support line."""
    message = make_message(user_id=101, username="newcomer", message_id=2001)

    await messages_handler.handle_message(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    assert "🌱" in reply_text
    assert t("supported_all_time", lang="ru", count=0) in reply_text


async def test_post_message_regular_includes_all_time_line(
    patch_messages_session: AsyncSession,
    patch_notify_users,
):
    """Regular user post response should include explicit all-time support line."""
    user = User(
        telegram_id=202,
        username="regular",
        display_name="Regular User",
        first_post_at=datetime.utcnow(),
    )
    user_karma = UserKarma(user_id=202, chat_id=-1001234567890, karma_total=7)
    patch_messages_session.add_all([user, user_karma])
    await patch_messages_session.commit()

    message = make_message(user_id=202, username="regular", message_id=2002)

    await messages_handler.handle_message(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    assert "🌱" not in reply_text
    assert "🎖️" not in reply_text
    assert t("supported_all_time", lang="ru", count=7) in reply_text


async def test_post_message_veteran_includes_all_time_line(
    patch_messages_session: AsyncSession,
    patch_notify_users,
):
    """Veteran post response should include explicit all-time support line."""
    user = User(
        telegram_id=303,
        username="veteran",
        display_name="Veteran User",
        first_post_at=datetime.utcnow(),
    )
    user_karma = UserKarma(user_id=303, chat_id=-1001234567890, karma_total=50)
    patch_messages_session.add_all([user, user_karma])
    await patch_messages_session.commit()

    message = make_message(user_id=303, username="veteran", message_id=2003)

    await messages_handler.handle_message(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    assert "🎖️50 - поддержал других за всё время" in reply_text
    assert t("supported_all_time", lang="ru", count=50) in reply_text


async def test_post_message_english_includes_all_time_line(
    patch_messages_session: AsyncSession,
    patch_notify_users,
):
    """English post response should include explicit all-time support line."""
    settings = GroupSettings(chat_id=-1001234567890, language="en")
    user = User(
        telegram_id=404,
        username="english_user",
        display_name="English User",
        first_post_at=datetime.utcnow(),
    )
    user_karma = UserKarma(user_id=404, chat_id=-1001234567890, karma_total=5)
    patch_messages_session.add_all([settings, user, user_karma])
    await patch_messages_session.commit()

    message = make_message(user_id=404, username="english_user", message_id=2004)

    await messages_handler.handle_message(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    assert t("asks_support", lang="en") in reply_text
    assert t("supported_all_time", lang="en", count=5) in reply_text
