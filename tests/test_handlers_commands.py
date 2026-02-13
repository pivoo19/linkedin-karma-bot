"""Tests for command handlers access rules and key flows."""

from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers import commands as commands_handler
from bot.i18n import t
from bot.models import GroupSettings, User, UserKarma


@pytest.fixture
def patch_commands_session(monkeypatch, async_session: AsyncSession):
    """Patch handler session provider to use the test session."""

    @asynccontextmanager
    async def _get_session():
        yield async_session

    monkeypatch.setattr(commands_handler, "get_session", _get_session)
    return async_session


def make_message(*, text: str, chat_type: str, chat_id: int, user_id: int = 111):
    """Create a minimal message object for command handler tests."""
    return SimpleNamespace(
        text=text,
        chat=SimpleNamespace(type=chat_type, id=chat_id),
        from_user=SimpleNamespace(
            id=user_id,
            username="tester",
            first_name="Test",
            last_name=None,
        ),
        reply=AsyncMock(),
        bot=SimpleNamespace(),
    )


@pytest.mark.parametrize(
    ("handler", "text"),
    [
        (commands_handler.cmd_karma, "/karma"),
        (commands_handler.cmd_top, "/top"),
        (commands_handler.cmd_top_all, "/top_all"),
        (commands_handler.cmd_stats, "/stats"),
    ],
)
async def test_group_commands_require_admin_for_non_admin_users(
    patch_commands_session: AsyncSession,
    monkeypatch,
    handler,
    text,
):
    """Group commands should return admin-only message for non-admin users."""
    is_admin_mock = AsyncMock(return_value=False)
    monkeypatch.setattr(commands_handler, "is_admin", is_admin_mock)

    message = make_message(
        text=text,
        chat_type="supergroup",
        chat_id=-1001234567890,
    )

    await handler(message)

    message.reply.assert_awaited_once_with(t("admin_only", lang="ru"))
    assert is_admin_mock.await_count == 1


@pytest.mark.parametrize(
    ("handler", "text", "expected_text"),
    [
        (commands_handler.cmd_top, "/top", t("no_data", lang="ru")),
        (commands_handler.cmd_top_all, "/top_all", t("no_data", lang="ru")),
        (commands_handler.cmd_stats, "/stats", t("stats_title", lang="ru")),
    ],
)
async def test_group_commands_work_for_admin_with_empty_data(
    patch_commands_session: AsyncSession,
    monkeypatch,
    handler,
    text,
    expected_text,
):
    """Admin users should pass access check and get regular command response."""
    monkeypatch.setattr(commands_handler, "is_admin", AsyncMock(return_value=True))

    message = make_message(
        text=text,
        chat_type="supergroup",
        chat_id=-1001234567890,
    )

    await handler(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    assert expected_text in reply_text
    if handler is commands_handler.cmd_stats:
        assert t("of_which_first_hour", lang="ru", count=0) in reply_text


async def test_group_karma_works_for_admin(
    patch_commands_session: AsyncSession,
    monkeypatch,
):
    """Admin should be able to run /karma in group and get stats message."""
    monkeypatch.setattr(commands_handler, "is_admin", AsyncMock(return_value=True))

    message = make_message(
        text="/karma",
        chat_type="supergroup",
        chat_id=-1001234567890,
    )

    await commands_handler.cmd_karma(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    expected_response = (
        f"📊 {t('your_karma', lang='ru')} @tester\n\n"
        f"{t('weekly', lang='ru')}: 0\n"
        f"{t('of_which_first_hour', lang='ru', count=0)}\n"
        f"{t('total', lang='ru')}: 0\n"
        f"{t('supported_all_time', lang='ru', count=0)}\n"
        f"{t('of_which_first_hour', lang='ru', count=0)}"
    )
    assert reply_text == expected_response


async def test_private_karma_bypasses_admin_check(
    patch_commands_session: AsyncSession,
    monkeypatch,
):
    """Private /karma should not call admin check and should return data/no-data."""
    is_admin_mock = AsyncMock(return_value=False)
    monkeypatch.setattr(commands_handler, "is_admin", is_admin_mock)

    message = make_message(
        text="/karma",
        chat_type="private",
        chat_id=111,
    )

    await commands_handler.cmd_karma(message)

    assert is_admin_mock.await_count == 0
    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    assert t("no_data", lang="ru") in reply_text


async def test_private_karma_includes_all_time_support_for_each_chat(
    patch_commands_session: AsyncSession,
    monkeypatch,
):
    """Private /karma should show explicit all-time support line in chat block."""
    monkeypatch.setattr(commands_handler, "is_admin", AsyncMock(return_value=False))

    user = User(
        telegram_id=111,
        username="tester",
        display_name="Test User",
        first_post_at=datetime.utcnow(),
    )
    user_karma = UserKarma(user_id=111, chat_id=-1001234567890, karma_total=7)
    settings = GroupSettings(chat_id=-1001234567890, language="ru")
    patch_commands_session.add_all([user, user_karma, settings])
    await patch_commands_session.commit()

    message = make_message(
        text="/karma",
        chat_type="private",
        chat_id=111,
    )
    message.bot.get_chat = AsyncMock(
        return_value=SimpleNamespace(title="Test Group")
    )

    await commands_handler.cmd_karma(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    expected_response = (
        f"📊 {t('your_karma', lang='ru')} @tester\n\n"
        f"💬 Test Group:\n"
        f"  {t('weekly', lang='ru')}: 0\n"
        f"  {t('of_which_first_hour', lang='ru', count=0)}\n"
        f"  {t('total', lang='ru')}: 7\n"
        f"  {t('supported_all_time', lang='ru', count=7)}\n"
        f"  {t('of_which_first_hour', lang='ru', count=0)}\n\n"
    )
    assert reply_text == expected_response


async def test_group_karma_english_includes_full_format(
    patch_commands_session: AsyncSession,
    monkeypatch,
):
    """Group /karma should include weekly + total + all-time in English."""
    monkeypatch.setattr(commands_handler, "is_admin", AsyncMock(return_value=True))

    user = User(
        telegram_id=222,
        username="tester",
        display_name="Test User",
        first_post_at=datetime.utcnow(),
    )
    user_karma = UserKarma(user_id=222, chat_id=-1001234567890, karma_total=5)
    settings = GroupSettings(chat_id=-1001234567890, language="en")
    patch_commands_session.add_all([user, user_karma, settings])
    await patch_commands_session.commit()

    message = make_message(
        text="/karma",
        chat_type="supergroup",
        chat_id=-1001234567890,
        user_id=222,
    )

    await commands_handler.cmd_karma(message)

    message.reply.assert_awaited_once()
    reply_text = message.reply.await_args.args[0]
    expected_response = (
        f"📊 {t('your_karma', lang='en')} @tester\n\n"
        f"{t('weekly', lang='en')}: 0\n"
        f"{t('of_which_first_hour', lang='en', count=0)}\n"
        f"{t('total', lang='en')}: 5\n"
        f"{t('supported_all_time', lang='en', count=5)}\n"
        f"{t('of_which_first_hour', lang='en', count=0)}"
    )
    assert reply_text == expected_response
