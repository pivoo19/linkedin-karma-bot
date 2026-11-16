"""Tests for forum topic filtering and karma topic commands."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import TopicRepository
from bot.handlers import topics as topics_handler
from bot.handlers.topics import GENERAL_TOPIC_ID, KarmaTopicFilter, topic_id_of

FORUM_CHAT_ID = -1001234567890


@pytest.fixture
def patch_topics_session(monkeypatch, async_session: AsyncSession):
    """Patch the topics module session provider to use the test session."""

    @asynccontextmanager
    async def _get_session():
        yield async_session

    monkeypatch.setattr(topics_handler, "get_session", _get_session)
    return async_session


def make_message(
    *,
    text: str = "hello",
    chat_type: str = "supergroup",
    chat_id: int = FORUM_CHAT_ID,
    is_forum: bool | None = True,
    thread_id: int | None = None,
    user_id: int = 111,
):
    """Create a minimal message object; thread_id=None means the General topic."""
    return SimpleNamespace(
        text=text,
        chat=SimpleNamespace(type=chat_type, id=chat_id, is_forum=is_forum),
        message_thread_id=thread_id,
        is_topic_message=True if thread_id is not None and is_forum else None,
        from_user=SimpleNamespace(id=user_id, username="tester", first_name="Test", last_name=None),
        reply=AsyncMock(),
        bot=SimpleNamespace(),
    )


def test_topic_id_of_topic_message():
    assert topic_id_of(make_message(thread_id=7)) == 7


def test_topic_id_of_general():
    assert topic_id_of(make_message(thread_id=None)) == GENERAL_TOPIC_ID == 1


async def test_filter_passes_private_chat(patch_topics_session):
    message = make_message(chat_type="private", chat_id=111, is_forum=None)
    assert await KarmaTopicFilter()(message) is True


async def test_filter_passes_non_forum_supergroup_reply(monkeypatch):
    def _fail():
        raise AssertionError("DB must not be queried for non-forum chats")

    monkeypatch.setattr(topics_handler, "get_session", _fail)
    message = make_message(is_forum=None, thread_id=42)
    message.message_thread_id = 42  # replies in non-forum supergroups carry a thread id
    assert await KarmaTopicFilter()(message) is True


async def test_filter_blocks_disabled_topic(patch_topics_session):
    assert await KarmaTopicFilter()(make_message(thread_id=7)) is False


async def test_filter_passes_enabled_topic(patch_topics_session):
    await TopicRepository(patch_topics_session).enable(FORUM_CHAT_ID, 7)
    assert await KarmaTopicFilter()(make_message(thread_id=7)) is True
    assert await KarmaTopicFilter()(make_message(thread_id=8)) is False


async def test_filter_passes_enabled_general(patch_topics_session):
    await TopicRepository(patch_topics_session).enable(FORUM_CHAT_ID, GENERAL_TOPIC_ID)
    assert await KarmaTopicFilter()(make_message(thread_id=None)) is True


async def test_filter_passes_message_without_chat():
    message = make_message()
    message.chat = None
    assert await KarmaTopicFilter()(message) is True


# --- /karma_on, /karma_off, /karma_topics, /about_karma ---------------------

from bot.handlers import commands as commands_handler  # noqa: E402
from bot.i18n import t  # noqa: E402
from bot.models import GroupSettings  # noqa: E402
from bot.services.rules import build_rules_text  # noqa: E402


@pytest.fixture
def admin(monkeypatch):
    mock = AsyncMock(return_value=True)
    monkeypatch.setattr(topics_handler, "is_admin", mock)
    return mock


def replies(message) -> list[str]:
    return [call.args[0] for call in message.reply.await_args_list]


async def test_karma_on_non_forum_replies_forum_only(patch_topics_session, admin):
    message = make_message(text="/karma_on", is_forum=None)
    await topics_handler.cmd_karma_on(message)
    assert replies(message) == [t("forum_only_command", lang="ru")]
    assert await TopicRepository(patch_topics_session).list_topics(FORUM_CHAT_ID) == []


async def test_karma_on_non_admin_rejected(patch_topics_session, monkeypatch):
    monkeypatch.setattr(topics_handler, "is_admin", AsyncMock(return_value=False))
    message = make_message(text="/karma_on", thread_id=7)
    await topics_handler.cmd_karma_on(message)
    assert replies(message) == [t("admin_only", lang="ru")]
    assert await TopicRepository(patch_topics_session).list_topics(FORUM_CHAT_ID) == []


async def test_karma_on_enables_and_sends_rules(patch_topics_session, admin):
    message = make_message(text="/karma_on", thread_id=7)
    await topics_handler.cmd_karma_on(message)
    assert replies(message) == [
        t("karma_topic_enabled", lang="ru"),
        build_rules_text("ru", 0),
    ]
    assert await TopicRepository(patch_topics_session).list_topics(FORUM_CHAT_ID) == [7]


async def test_karma_on_general_enables_topic_1(patch_topics_session, admin):
    await topics_handler.cmd_karma_on(make_message(text="/karma_on", thread_id=None))
    assert await TopicRepository(patch_topics_session).list_topics(FORUM_CHAT_ID) == [1]


async def test_karma_on_twice_ok(patch_topics_session, admin):
    await topics_handler.cmd_karma_on(make_message(text="/karma_on", thread_id=7))
    message = make_message(text="/karma_on", thread_id=7)
    await topics_handler.cmd_karma_on(message)
    assert replies(message)[-1] == build_rules_text("ru", 0)
    assert await TopicRepository(patch_topics_session).list_topics(FORUM_CHAT_ID) == [7]


async def test_karma_on_uses_group_language(patch_topics_session, admin):
    patch_topics_session.add(GroupSettings(chat_id=FORUM_CHAT_ID, language="en", post_cost=2))
    await patch_topics_session.commit()
    message = make_message(text="/karma_on", thread_id=7)
    await topics_handler.cmd_karma_on(message)
    assert replies(message) == [
        t("karma_topic_enabled", lang="en"),
        build_rules_text("en", 2),
    ]


async def test_karma_off_disables(patch_topics_session, admin):
    await TopicRepository(patch_topics_session).enable(FORUM_CHAT_ID, 7)
    message = make_message(text="/karma_off", thread_id=7)
    await topics_handler.cmd_karma_off(message)
    assert replies(message) == [t("karma_topic_disabled", lang="ru")]
    assert await TopicRepository(patch_topics_session).list_topics(FORUM_CHAT_ID) == []


async def test_karma_off_not_enabled(patch_topics_session, admin):
    message = make_message(text="/karma_off", thread_id=7)
    await topics_handler.cmd_karma_off(message)
    assert replies(message) == [t("karma_topic_not_enabled", lang="ru")]


async def test_karma_topics_lists_links(patch_topics_session, admin):
    repo = TopicRepository(patch_topics_session)
    await repo.enable(FORUM_CHAT_ID, 1)
    await repo.enable(FORUM_CHAT_ID, 7)
    message = make_message(text="/karma_topics", thread_id=3)
    await topics_handler.cmd_karma_topics(message)
    (text,) = replies(message)
    assert "https://t.me/c/1234567890/7" in text
    assert t("karma_topic_general", lang="ru") in text


async def test_karma_topics_empty(patch_topics_session, admin):
    message = make_message(text="/karma_topics", thread_id=3)
    await topics_handler.cmd_karma_topics(message)
    assert replies(message) == [t("karma_topics_empty", lang="ru")]


@pytest.fixture
def patch_commands_session(monkeypatch, async_session: AsyncSession):
    @asynccontextmanager
    async def _get_session():
        yield async_session

    monkeypatch.setattr(commands_handler, "get_session", _get_session)
    return async_session


async def test_about_karma_in_group_uses_group_settings(patch_commands_session):
    patch_commands_session.add(GroupSettings(chat_id=FORUM_CHAT_ID, language="en"))
    await patch_commands_session.commit()
    message = make_message(text="/about_karma", thread_id=7)
    await commands_handler.cmd_about_karma(message)
    assert replies(message) == [build_rules_text("en", 0)]


async def test_about_karma_private_ru(patch_commands_session):
    message = make_message(text="/about_karma", chat_type="private", chat_id=111, is_forum=None)
    await commands_handler.cmd_about_karma(message)
    assert replies(message) == [build_rules_text("ru", 0)]


def test_routers_order_and_filters():
    from bot.handlers import get_routers

    def has_topic_filter(router) -> bool:
        return any(isinstance(f.callback, KarmaTopicFilter) for f in router.message._handler.filters)

    routers = get_routers()
    assert [r.name for r in routers] == ["topics", "reactions", "topic_gated"]
    by_name = {r.name: r for r in routers}
    assert not has_topic_filter(by_name["topics"])
    assert not has_topic_filter(by_name["reactions"])

    gated = by_name["topic_gated"]
    assert has_topic_filter(gated)
    assert [r.name for r in gated.sub_routers] == ["admin", "commands", "messages"]
    for child in gated.sub_routers:
        assert not has_topic_filter(child), child.name


# --- Real Dispatcher: the topic check runs once per message -----------------

from datetime import datetime, timezone  # noqa: E402

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.types import Update  # noqa: E402

from bot.handlers import messages as messages_handler  # noqa: E402


@pytest.fixture(scope="session")
def dispatcher():
    """Build the Dispatcher once: aiogram forbids attaching a router to two parents."""
    from bot.handlers import get_routers

    dp = Dispatcher()
    for router in get_routers():
        dp.include_router(router)
    return dp


@pytest.fixture
async def bot():
    bot = Bot(token="42:TEST")
    yield bot
    await bot.session.close()


@pytest.fixture
def topic_checks(monkeypatch):
    """Count topic checks; topics 7 and 1 (General) are enabled."""
    calls: list[tuple[int, int]] = []

    @asynccontextmanager
    async def _get_session():
        yield None

    async def _is_enabled(self, chat_id: int, topic_id: int) -> bool:
        calls.append((chat_id, topic_id))
        return topic_id in (1, 7)

    monkeypatch.setattr(topics_handler, "get_session", _get_session)
    monkeypatch.setattr(TopicRepository, "is_enabled", _is_enabled)
    return calls


@pytest.fixture
def link_handler_calls(monkeypatch):
    """Count deliveries to the LinkedIn link handler without touching the DB."""
    calls: list[str] = []

    def _extract(message):
        calls.append(message.text)
        return []

    monkeypatch.setattr(messages_handler, "extract_linkedin_urls_from_message", _extract)
    return calls


def make_update(*, is_forum: bool, thread_id: int | None, sticker: bool = False) -> Update:
    chat = {"id": FORUM_CHAT_ID, "type": "supergroup", "title": "Test"}
    if is_forum:
        chat["is_forum"] = True
    message = {
        "message_id": 10,
        "date": int(datetime.now(timezone.utc).timestamp()),
        "chat": chat,
        "from": {"id": 111, "is_bot": False, "first_name": "Test"},
    }
    if thread_id is not None:
        message["message_thread_id"] = thread_id
        if is_forum:
            message["is_topic_message"] = True
    if sticker:
        message["sticker"] = {
            "file_id": "f", "file_unique_id": "u", "type": "regular",
            "width": 512, "height": 512, "is_animated": False, "is_video": False,
        }
    else:
        message["text"] = "hello"
    return Update.model_validate({"update_id": 1, "message": message})


@pytest.mark.parametrize("sticker", [False, True], ids=["text", "sticker"])
@pytest.mark.parametrize("thread_id", [7, 8], ids=["enabled", "disabled"])
async def test_forum_message_checks_topic_once(
    dispatcher, bot, topic_checks, link_handler_calls, sticker, thread_id
):
    await dispatcher.feed_update(bot, make_update(is_forum=True, thread_id=thread_id, sticker=sticker))
    assert topic_checks == [(FORUM_CHAT_ID, thread_id)]
    expected = 1 if (thread_id == 7 and not sticker) else 0
    assert len(link_handler_calls) == expected


async def test_forum_general_message_checked_as_topic_1(
    dispatcher, bot, topic_checks, link_handler_calls
):
    await dispatcher.feed_update(bot, make_update(is_forum=True, thread_id=None))
    assert topic_checks == [(FORUM_CHAT_ID, 1)]
    assert link_handler_calls == ["hello"]


async def test_non_forum_reply_with_thread_id_skips_topic_check(
    dispatcher, bot, topic_checks, link_handler_calls
):
    await dispatcher.feed_update(bot, make_update(is_forum=False, thread_id=42))
    assert topic_checks == []
    assert link_handler_calls == ["hello"]
