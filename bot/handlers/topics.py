"""Per-topic activation of the karma bot in forum supergroups.

In forum supergroups (chats with topics) the bot works only in topics that a group
admin enabled with /karma_on. Regular groups, supergroups without topics and private
chats are not affected.
"""

import logging

from aiogram import Router
from aiogram.filters import Command, Filter
from aiogram.types import Message

from bot.database import get_session
from bot.database.repositories import SettingsRepository, TopicRepository
from bot.handlers.admin import is_admin
from bot.i18n import t
from bot.services.rules import build_rules_text

logger = logging.getLogger(__name__)

# Not filtered by KarmaTopicFilter: these commands must work in disabled topics.
router = Router(name="topics")

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


def topic_link(chat_id: int, topic_id: int) -> str:
    """Return a t.me link to a forum topic (works for members of private groups)."""
    internal_id = str(chat_id).removeprefix("-100")
    return f"https://t.me/c/{internal_id}/{topic_id}"


async def _check_forum_admin(message: Message, lang: str) -> bool:
    """Reply and return False unless this is a forum and the sender is an admin."""
    if not is_forum(message):
        await message.reply(t("forum_only_command", lang=lang))
        return False
    if not await is_admin(message):
        await message.reply(t("admin_only", lang=lang))
        return False
    return True


@router.message(Command("karma_on"))
async def cmd_karma_on(message: Message):
    """Enable the bot in the current forum topic and post the game rules."""
    if not message.from_user or not message.chat:
        return
    async with get_session() as session:
        settings, _ = await SettingsRepository(session).get_or_create(message.chat.id)
        lang = settings.language
        if not await _check_forum_admin(message, lang):
            return
        topic_id = topic_id_of(message)
        await TopicRepository(session).enable(message.chat.id, topic_id)
        logger.info(f"Karma enabled in chat {message.chat.id} topic {topic_id}")
        await message.reply(t("karma_topic_enabled", lang=lang))
        await message.reply(build_rules_text(lang, settings.post_cost))


@router.message(Command("karma_off"))
async def cmd_karma_off(message: Message):
    """Disable the bot in the current forum topic."""
    if not message.from_user or not message.chat:
        return
    async with get_session() as session:
        settings, _ = await SettingsRepository(session).get_or_create(message.chat.id)
        lang = settings.language
        if not await _check_forum_admin(message, lang):
            return
        topic_id = topic_id_of(message)
        if await TopicRepository(session).disable(message.chat.id, topic_id):
            logger.info(f"Karma disabled in chat {message.chat.id} topic {topic_id}")
            await message.reply(t("karma_topic_disabled", lang=lang))
        else:
            await message.reply(t("karma_topic_not_enabled", lang=lang))


@router.message(Command("karma_topics"))
async def cmd_karma_topics(message: Message):
    """List forum topics where the bot is enabled."""
    if not message.from_user or not message.chat:
        return
    async with get_session() as session:
        settings, _ = await SettingsRepository(session).get_or_create(message.chat.id)
        lang = settings.language
        if not await _check_forum_admin(message, lang):
            return
        topic_ids = await TopicRepository(session).list_topics(message.chat.id)
    if not topic_ids:
        await message.reply(t("karma_topics_empty", lang=lang))
        return
    lines = []
    for topic_id in topic_ids:
        link = topic_link(message.chat.id, topic_id)
        if topic_id == GENERAL_TOPIC_ID:
            lines.append(f"• {t('karma_topic_general', lang=lang)}: {link}")
        else:
            lines.append(f"• {link}")
    await message.reply(t("karma_topics_list", lang=lang, topics="\n".join(lines)))
