"""Admin command handlers.

This module handles admin-only commands for group configuration.
"""

import csv
import io
from datetime import datetime, timedelta
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, ChatMemberOwner, ChatMemberAdministrator
from sqlalchemy import select, func, and_

from bot.database import get_session
from bot.models import User, Post, Reaction, UserKarma
from bot.services.user import UserService
from bot.services.stats import StatsService
from bot.services.linkedin import extract_linkedin_urls
from bot.database.repositories import ReactionRepository, UserKarmaRepository
from bot.i18n import t
import logging


router = Router(name="admin")


async def is_admin(message: Message) -> bool:
    """Check if user is admin in the chat.

    Args:
        message: Message from user

    Returns:
        True if user is admin, False otherwise
    """
    if not message.from_user or not message.chat:
        return False

    try:
        member = await message.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )
        return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
    except Exception:
        return False


@router.message(Command("set_lang"))
async def cmd_set_lang(message: Message):
    """Set group language.

    Usage: /set_lang ru|en

    Args:
        message: Incoming command message
    """
    if not await is_admin(message):
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("admin_only", lang=settings.language))
        return

    if not message.text or len(message.text.split()) < 2:
        await message.reply("❌ /set_lang ru|en")
        return

    lang = message.text.split()[1].lower()
    if lang not in ['ru', 'en']:
        await message.reply("❌ ru | en")
        return

    async with get_session() as session:
        user_service = UserService(session)
        await user_service.update_settings(
            chat_id=message.chat.id,
            language=lang
        )

        await message.reply(t("language_set", lang=lang, value=lang))


@router.message(Command("set_period"))
async def cmd_set_period(message: Message):
    """Set karma period in days.

    Usage: /set_period N

    Args:
        message: Incoming command message
    """
    if not await is_admin(message):
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("admin_only", lang=settings.language))
        return

    if not message.text or len(message.text.split()) < 2:
        await message.reply("❌ /set_period N")
        return

    try:
        period = int(message.text.split()[1])
        if period < 1 or period > 365:
            await message.reply("❌ 1-365")
            return
    except ValueError:
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("invalid_value", lang=settings.language))
        return

    async with get_session() as session:
        user_service = UserService(session)
        await user_service.update_settings(
            chat_id=message.chat.id,
            karma_period_days=period
        )
        settings = await user_service.get_or_create_settings(message.chat.id)

        await message.reply(t("karma_period_set", lang=settings.language, value=period))


@router.message(Command("set_veteran"))
async def cmd_set_veteran(message: Message):
    """Set veteran threshold.

    Usage: /set_veteran N

    Args:
        message: Incoming command message
    """
    if not await is_admin(message):
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("admin_only", lang=settings.language))
        return

    if not message.text or len(message.text.split()) < 2:
        await message.reply("❌ /set_veteran N")
        return

    try:
        threshold = int(message.text.split()[1])
        if threshold < 0:
            await message.reply("❌ >= 0")
            return
    except ValueError:
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("invalid_value", lang=settings.language))
        return

    async with get_session() as session:
        user_service = UserService(session)
        await user_service.update_settings(
            chat_id=message.chat.id,
            veteran_threshold=threshold
        )
        settings = await user_service.get_or_create_settings(message.chat.id)

        await message.reply(t("veteran_threshold_set", lang=settings.language, value=threshold))


@router.message(Command("set_post_cost"))
async def cmd_set_post_cost(message: Message):
    """Set post cost in karma points.

    Usage: /set_post_cost N

    Args:
        message: Incoming command message
    """
    if not await is_admin(message):
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("admin_only", lang=settings.language))
        return

    if not message.text or len(message.text.split()) < 2:
        await message.reply("❌ /set_post_cost N")
        return

    try:
        cost = int(message.text.split()[1])
        if cost < 0:
            await message.reply("❌ >= 0")
            return
    except ValueError:
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("invalid_value", lang=settings.language))
        return

    async with get_session() as session:
        user_service = UserService(session)
        await user_service.update_settings(
            chat_id=message.chat.id,
            post_cost=cost
        )
        settings = await user_service.get_or_create_settings(message.chat.id)

        await message.reply(t("post_cost_set", lang=settings.language, value=cost))


@router.message(Command("reset_karma"))
async def cmd_reset_karma(message: Message):
    """Reset user's karma to zero.

    Usage: /reset_karma @username

    Args:
        message: Incoming command message
    """
    if not await is_admin(message):
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("admin_only", lang=settings.language))
        return

    if not message.text or len(message.text.split()) < 2:
        await message.reply("❌ /reset_karma @username")
        return

    username = message.text.split()[1].lstrip('@')

    async with get_session() as session:
        user_service = UserService(session)
        settings = await user_service.get_or_create_settings(message.chat.id)
        lang = settings.language

        # Find user
        user = await user_service.get_user_by_username(username)
        if not user:
            await message.reply(t("user_not_found", lang=lang))
            return

        # Reset karma in this chat
        karma_repo = UserKarmaRepository(session)
        await karma_repo.reset_karma(
            user_id=user.telegram_id,
            chat_id=message.chat.id
        )

        await message.reply(f"✅ @{username} karma = 0")


@router.message(Command("export"))
async def cmd_export(message: Message):
    """Export group statistics as CSV file.

    Args:
        message: Incoming command message
    """
    if not await is_admin(message):
        async with get_session() as session:
            user_service = UserService(session)
            settings = await user_service.get_or_create_settings(message.chat.id)
            await message.reply(t("admin_only", lang=settings.language))
        return

    if not message.chat:
        return

    async with get_session() as session:
        user_service = UserService(session)
        settings = await user_service.get_or_create_settings(message.chat.id)
        lang = settings.language

        # Get all users with their stats who have posted in this chat
        result = await session.execute(
            select(
                User.telegram_id,
                User.username,
                User.display_name,
                UserKarma.karma_total,
                User.first_post_at,
                func.count(func.distinct(Post.id)).label('total_posts')
            )
            .join(Post, Post.author_id == User.telegram_id)
            .outerjoin(UserKarma, and_(
                UserKarma.user_id == User.telegram_id,
                UserKarma.chat_id == message.chat.id
            ))
            .where(Post.chat_id == message.chat.id)
            .group_by(
                User.telegram_id,
                User.username,
                User.display_name,
                UserKarma.karma_total,
                User.first_post_at
            )
            .order_by(UserKarma.karma_total.desc().nulls_last())
        )

        users = result.all()

        if not users:
            await message.reply(t("no_data", lang=lang))
            return

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'User ID',
            'Username',
            'Display Name',
            'Total Karma',
            'First Post Date',
            'Total Posts'
        ])

        # Write data
        for user_data in users:
            telegram_id, username, display_name, karma, first_post_at, posts = user_data
            writer.writerow([
                telegram_id,
                username or '',
                display_name or '',
                karma or 0,  # Handle NULL karma
                first_post_at.strftime('%Y-%m-%d %H:%M:%S') if first_post_at else '',
                posts
            ])

        # Get CSV content
        csv_content = output.getvalue().encode('utf-8')
        output.close()

        # Send file
        file = BufferedInputFile(
            csv_content,
            filename=f"karma_stats_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        await message.reply_document(
            document=file,
            caption=f"📊 {t('stats_title', lang=lang)}"
        )