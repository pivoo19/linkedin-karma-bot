"""Per-topic activation of the karma bot in forum supergroups.

In forum supergroups (chats with topics) the bot works only in topics that a group
admin enabled with /karma_on. Regular groups, supergroups without topics and private
chats are not affected.
"""

from aiogram.filters import Filter
from aiogram.types import Message

from bot.database import get_session
from bot.database.repositories import TopicRepository

# Telegram's General topic has id 1, but its messages carry no message_thread_id.
GENERAL_TOPIC_ID = 1


def is_forum(message: Message) -> bool:
    """Return True if the message comes from a forum supergroup."""
    return bool(message.chat and getattr(message.chat, "is_forum", None))


def topic_id_of(message: Message) -> int:
    """Return the forum topic id of a message (General topic -> 1)."""
    if message.is_topic_message and message.message_thread_id:
        return message.message_thread_id
    return GENERAL_TOPIC_ID


class KarmaTopicFilter(Filter):
    """Pass non-forum chats; in forums pass only enabled topics."""

    async def __call__(self, message: Message) -> bool:
        if not is_forum(message):
            return True
        async with get_session() as session:
            return await TopicRepository(session).is_enabled(
                message.chat.id, topic_id_of(message)
            )
