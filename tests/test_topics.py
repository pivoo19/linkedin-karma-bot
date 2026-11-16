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
