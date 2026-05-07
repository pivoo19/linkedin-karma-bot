"""User command handlers.

This module handles user commands like /karma, /top, /stats, and /help.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func, and_, distinct
from datetime import datetime, timedelta

from bot.database import get_session
from bot.models import User, Reaction, Post, UserKarma
from bot.services.user import UserService
from bot.services.karma import KarmaService
from bot.services.stats import StatsService
from bot.database.repositories import UserKarmaRepository
from bot.i18n import t
from bot.handlers.admin import is_admin


router = Router(name="commands")


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command.

    Works only in private messages.

    Args:
        message: Incoming command message
    """
    if not message.from_user or not message.chat:
        return

    # Only allow in private messages
    if message.chat.type != "private":
        return

    try:
        async with get_session() as session:
            user_service = UserService(session)
            lang = "ru"  # Default language for private messages

            # Register user
            await user_service.get_or_create_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )

            welcome_text = t("welcome", lang=lang) + "\n\n" + t("commands_list", lang=lang)
            await message.reply(welcome_text)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in /start command: {e}", exc_info=True)
        try:
            await message.reply(t("error_occurred", lang="ru"))
        except:
            pass


@router.message(Command("karma"))
async def cmd_karma(message: Message):
    """Show user's karma statistics.

    Usage:
    - /karma - show own karma
    - /karma @username - show user's karma

    In private messages: shows karma for all groups
    In groups: shows karma for this group only

    Args:
        message: Incoming command message
    """
    if not message.from_user or not message.chat:
        return

    async with get_session() as session:
        user_service = UserService(session)
        karma_service = KarmaService(session)
        karma_repo = UserKarmaRepository(session)

        # Check if it's a private message
        is_private = message.chat.type == "private"
        
        # In groups, only admins can use this command
        if not is_private:
            if not await is_admin(message):
                settings = await user_service.get_or_create_settings(message.chat.id)
                await message.reply(t("admin_only", lang=settings.language))
                return

        # Get default language (ru) for private messages, or group settings for groups
        if is_private:
            lang = "ru"  # Default language for private messages
        else:
            settings = await user_service.get_or_create_settings(message.chat.id)
            lang = settings.language

        # Check if username is provided
        target_user = None
        if message.text and len(message.text.split()) > 1:
            # Extract username
            username = message.text.split()[1].lstrip('@')
            target_user = await user_service.get_user_by_username(username)

            if not target_user:
                await message.reply(t("user_not_found", lang=lang))
                return
        else:
            # Show own karma
            target_user = await user_service.get_or_create_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )

        # Format username for display
        username_display = f"@{target_user.username}" if target_user.username else (
            target_user.display_name or "User"
        )

        if is_private:
            # In private messages, show karma for all groups
            # Get all chats where user has karma
            chats_query = (
                select(
                    UserKarma.chat_id,
                    UserKarma.karma_total
                )
                .where(UserKarma.user_id == target_user.telegram_id)
                .order_by(UserKarma.karma_total.desc())
            )
            result = await session.execute(chats_query)
            user_karmas = result.all()

            if not user_karmas:
                response = (
                    f"📊 {t('your_karma', lang=lang)} {username_display}\n\n"
                    f"{t('no_data', lang=lang)}"
                )
            else:
                response = f"📊 {t('your_karma', lang=lang)} {username_display}\n\n"
                
                # Get weekly karma for each chat
                for chat_id, total_karma in user_karmas:
                    total_karma_value = total_karma or 0

                    # Get chat settings for this group
                    chat_settings = await user_service.get_or_create_settings(chat_id)
                    
                    # Get weekly karma for this chat
                    weekly_karma = await karma_service.get_weekly_karma(
                        user_id=target_user.telegram_id,
                        chat_id=chat_id,
                        period_days=chat_settings.karma_period_days
                    )
                    weekly_first_day = await karma_service.get_weekly_first_day_karma(
                        user_id=target_user.telegram_id,
                        chat_id=chat_id,
                        period_days=chat_settings.karma_period_days
                    )
                    weekly_first_hour = await karma_service.get_weekly_first_hour_karma(
                        user_id=target_user.telegram_id,
                        chat_id=chat_id,
                        period_days=chat_settings.karma_period_days
                    )
                    total_first_day = await karma_service.get_total_first_day_karma(
                        user_id=target_user.telegram_id,
                        chat_id=chat_id
                    )
                    total_first_hour = await karma_service.get_total_first_hour_karma(
                        user_id=target_user.telegram_id,
                        chat_id=chat_id
                    )

                    stars = karma_service.karma_to_stars(weekly_karma)
                    karma_display = f"{stars} ({weekly_karma})" if stars else str(weekly_karma)

                    # Try to get chat title (we'll use chat_id as fallback)
                    try:
                        chat = await message.bot.get_chat(chat_id)
                        chat_name = chat.title or f"Chat {chat_id}"
                    except:
                        chat_name = f"Chat {chat_id}"

                    response += (
                        f"💬 {chat_name}:\n"
                        f"  {t('weekly', lang=lang)}: {karma_display}\n"
                        f"  {t('of_which_first_day', lang=lang, count=weekly_first_day)}\n"
                        f"  {t('of_which_first_hour', lang=lang, count=weekly_first_hour)}\n"
                        f"  {t('total', lang=lang)}: {total_karma_value}\n"
                        f"  {t('supported_all_time', lang=lang, count=total_karma_value, first_day=total_first_day)}\n\n"
                    )
        else:
            # In groups, show karma for this group only
            # Get group settings
            settings = await user_service.get_or_create_settings(message.chat.id)
            lang = settings.language
            
            weekly_karma = await karma_service.get_weekly_karma(
                user_id=target_user.telegram_id,
                chat_id=message.chat.id,
                period_days=settings.karma_period_days
            )
            weekly_first_day = await karma_service.get_weekly_first_day_karma(
                user_id=target_user.telegram_id,
                chat_id=message.chat.id,
                period_days=settings.karma_period_days
            )
            weekly_first_hour = await karma_service.get_weekly_first_hour_karma(
                user_id=target_user.telegram_id,
                chat_id=message.chat.id,
                period_days=settings.karma_period_days
            )
            total_first_day = await karma_service.get_total_first_day_karma(
                user_id=target_user.telegram_id,
                chat_id=message.chat.id
            )
            total_first_hour = await karma_service.get_total_first_hour_karma(
                user_id=target_user.telegram_id,
                chat_id=message.chat.id
            )

            # Get total karma for this chat
            total_karma = await karma_repo.get_total_karma(
                user_id=target_user.telegram_id,
                chat_id=message.chat.id
            )

            # Format response
            stars = karma_service.karma_to_stars(weekly_karma)
            karma_display = f"{stars} ({weekly_karma})" if stars else str(weekly_karma)

            response = (
                f"📊 {t('your_karma', lang=lang)} {username_display}\n\n"
                f"{t('weekly', lang=lang)}: {karma_display}\n"
                f"{t('of_which_first_day', lang=lang, count=weekly_first_day)}\n"
                f"{t('of_which_first_hour', lang=lang, count=weekly_first_hour)}\n"
                f"{t('total', lang=lang)}: {total_karma}\n"
                f"{t('supported_all_time', lang=lang, count=total_karma, first_day=total_first_day)}\n"
                f"{t('of_which_first_hour', lang=lang, count=total_first_hour)}"
            )

        await message.reply(response)


@router.message(Command("top"))
async def cmd_top(message: Message):
    """Show top 10 users by weekly karma.

    In private messages: shows top for all groups where user has karma
    In groups: shows top for this group only

    Args:
        message: Incoming command message
    """
    if not message.chat or not message.from_user:
        return

    async with get_session() as session:
        user_service = UserService(session)
        karma_service = KarmaService(session)
        
        # Check if it's a private message
        is_private = message.chat.type == "private"
        
        # In groups, only admins can use this command
        if not is_private:
            if not await is_admin(message):
                settings = await user_service.get_or_create_settings(message.chat.id)
                await message.reply(t("admin_only", lang=settings.language))
                return
        
        if is_private:
            # In private messages, show top for all groups where user has karma
            lang = "ru"  # Default language for private messages
            
            # Get all chats where user has karma
            chats_query = (
                select(UserKarma.chat_id)
                .where(UserKarma.user_id == message.from_user.id)
                .distinct()
            )
            result = await session.execute(chats_query)
            chat_ids = [row[0] for row in result.all()]
            
            if not chat_ids:
                await message.reply(t("no_data", lang=lang))
                return
            
            response = f"🏆 {t('top_weekly', lang=lang)}\n\n"
            
            # Get top for each chat
            for chat_id in chat_ids:
                # Get chat settings
                chat_settings = await user_service.get_or_create_settings(chat_id)
                period_start = datetime.utcnow() - timedelta(days=chat_settings.karma_period_days)
                
                # Get top users for this chat
                top_result = await session.execute(
                    select(
                        Reaction.user_id,
                        func.count(func.distinct(Reaction.post_id)).label('karma')
                    )
                    .join(Post, Reaction.post_id == Post.id)
                    .where(
                        and_(
                            Post.chat_id == chat_id,
                            Reaction.created_at >= period_start
                        )
                    )
                    .group_by(Reaction.user_id)
                    .order_by(func.count(func.distinct(Reaction.post_id)).desc())
                    .limit(10)
                )
                
                top_data = top_result.all()
                
                if top_data:
                    # Get chat name
                    try:
                        chat = await message.bot.get_chat(chat_id)
                        chat_name = chat.title or f"Chat {chat_id}"
                    except:
                        chat_name = f"Chat {chat_id}"
                    
                    response += f"💬 {chat_name}:\n"
                    
                    for i, (user_id, karma) in enumerate(top_data, 1):
                        user = await user_service.get_user_by_id(user_id)
                        if user:
                            username_display = f"@{user.username}" if user.username else (
                                user.display_name or "User"
                            )
                        else:
                            username_display = t("deleted_user", lang=lang)
                        
                        stars = karma_service.karma_to_stars(karma)
                        karma_display = f"{stars} ({karma})" if stars else str(karma)
                        weekly_first_hour = await karma_service.get_weekly_first_hour_karma(
                            user_id=user_id,
                            chat_id=chat_id,
                            period_days=chat_settings.karma_period_days
                        )
                        
                        response += (
                            f"  {i}. {username_display}: {karma_display} "
                            f"({t('of_which_first_hour', lang=lang, count=weekly_first_hour)})\n"
                        )
                    
                    response += "\n"
            
            await message.reply(response)
        else:
            # In groups, show top for this group only
            settings = await user_service.get_or_create_settings(message.chat.id)
            lang = settings.language

            # Get weekly karma for all users who supported posts
            period_start = datetime.utcnow() - timedelta(days=settings.karma_period_days)

            # Count unique posts supported per user in this chat
            result = await session.execute(
                select(
                    Reaction.user_id,
                    func.count(func.distinct(Reaction.post_id)).label('karma')
                )
                .join(Post, Reaction.post_id == Post.id)
                .where(
                    and_(
                        Post.chat_id == message.chat.id,
                        Reaction.created_at >= period_start
                    )
                )
                .group_by(Reaction.user_id)
                .order_by(func.count(func.distinct(Reaction.post_id)).desc())
                .limit(10)
            )

            top_data = result.all()

            if not top_data:
                await message.reply(t("no_data", lang=lang))
                return

            # Fetch user info for each user
            response = f"🏆 {t('top_weekly', lang=lang)}\n\n"

            for i, (user_id, karma) in enumerate(top_data, 1):
                user = await user_service.get_user_by_id(user_id)
                if user:
                    username_display = f"@{user.username}" if user.username else (
                        user.display_name or "User"
                    )
                else:
                    username_display = t("deleted_user", lang=lang)

                stars = karma_service.karma_to_stars(karma)
                karma_display = f"{stars} ({karma})" if stars else str(karma)
                weekly_first_hour = await karma_service.get_weekly_first_hour_karma(
                    user_id=user_id,
                    chat_id=message.chat.id,
                    period_days=settings.karma_period_days
                )

                response += (
                    f"{i}. {username_display}: {karma_display} "
                    f"({t('of_which_first_hour', lang=lang, count=weekly_first_hour)})\n"
                )

            await message.reply(response)


@router.message(Command("top_all"))
async def cmd_top_all(message: Message):
    """Show top 10 users by total karma.

    In private messages: shows top for all groups where user has karma
    In groups: shows top for this group only

    Args:
        message: Incoming command message
    """
    if not message.chat or not message.from_user:
        return

    async with get_session() as session:
        user_service = UserService(session)
        karma_service = KarmaService(session)
        
        # Check if it's a private message
        is_private = message.chat.type == "private"
        
        # In groups, only admins can use this command
        if not is_private:
            if not await is_admin(message):
                settings = await user_service.get_or_create_settings(message.chat.id)
                await message.reply(t("admin_only", lang=settings.language))
                return
        
        if is_private:
            # In private messages, show top for all groups where user has karma
            lang = "ru"  # Default language for private messages
            
            # Get all chats where user has karma
            chats_query = (
                select(UserKarma.chat_id)
                .where(UserKarma.user_id == message.from_user.id)
                .distinct()
            )
            result = await session.execute(chats_query)
            chat_ids = [row[0] for row in result.all()]
            
            if not chat_ids:
                await message.reply(t("no_data", lang=lang))
                return
            
            response = f"🏆 {t('top_all', lang=lang)}\n\n"
            
            # Get top for each chat
            for chat_id in chat_ids:
                # Get top users by total karma in this chat
                top_result = await session.execute(
                    select(
                        User.telegram_id,
                        User.username,
                        User.display_name,
                        func.coalesce(UserKarma.karma_total, 0).label('karma_total')
                    )
                    .join(UserKarma, UserKarma.user_id == User.telegram_id)
                    .where(UserKarma.chat_id == chat_id)
                    .order_by(UserKarma.karma_total.desc())
                    .limit(10)
                )
                
                top_users = top_result.all()
                
                if top_users:
                    # Get chat name
                    try:
                        chat = await message.bot.get_chat(chat_id)
                        chat_name = chat.title or f"Chat {chat_id}"
                    except:
                        chat_name = f"Chat {chat_id}"
                    
                    response += f"💬 {chat_name}:\n"
                    
                    for i, (telegram_id, username, display_name, karma) in enumerate(top_users, 1):
                        username_display = f"@{username}" if username else (display_name or "User")
                        karma_value = karma if karma is not None else 0
                        total_first_hour = await karma_service.get_total_first_hour_karma(
                            user_id=telegram_id,
                            chat_id=chat_id
                        )
                        response += (
                            f"  {i}. {username_display}: {karma_value} "
                            f"({t('of_which_first_hour', lang=lang, count=total_first_hour)})\n"
                        )
                    
                    response += "\n"
            
            await message.reply(response)
        else:
            # In groups, show top for this group only
            settings = await user_service.get_or_create_settings(message.chat.id)
            lang = settings.language

            # Get top users by total karma in this chat
            result = await session.execute(
                select(
                    User.telegram_id,
                    User.username,
                    User.display_name,
                    func.coalesce(UserKarma.karma_total, 0).label('karma_total')
                )
                .join(UserKarma, UserKarma.user_id == User.telegram_id)
                .where(UserKarma.chat_id == message.chat.id)
                .order_by(UserKarma.karma_total.desc())
                .limit(10)
            )

            top_users = result.all()

            if not top_users:
                await message.reply(t("no_data", lang=lang))
                return

            # Format response
            response = f"🏆 {t('top_all', lang=lang)}\n\n"

            for i, (telegram_id, username, display_name, karma) in enumerate(top_users, 1):
                username_display = f"@{username}" if username else (display_name or "User")
                karma_value = karma if karma is not None else 0
                total_first_hour = await karma_service.get_total_first_hour_karma(
                    user_id=telegram_id,
                    chat_id=message.chat.id
                )
                response += (
                    f"{i}. {username_display}: {karma_value} "
                    f"({t('of_which_first_hour', lang=lang, count=total_first_hour)})\n"
                )

            await message.reply(response)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show group statistics.

    In private messages: shows stats for all groups where user has karma
    In groups: shows stats for this group only

    Args:
        message: Incoming command message
    """
    if not message.chat or not message.from_user:
        return

    async with get_session() as session:
        user_service = UserService(session)
        stats_service = StatsService(session)
        
        # Check if it's a private message
        is_private = message.chat.type == "private"
        
        # In groups, only admins can use this command
        if not is_private:
            if not await is_admin(message):
                settings = await user_service.get_or_create_settings(message.chat.id)
                await message.reply(t("admin_only", lang=settings.language))
                return
        
        if is_private:
            # In private messages, show stats for all groups where user has karma
            lang = "ru"  # Default language for private messages
            
            # Get all chats where user has karma
            chats_query = (
                select(UserKarma.chat_id)
                .where(UserKarma.user_id == message.from_user.id)
                .distinct()
            )
            result = await session.execute(chats_query)
            chat_ids = [row[0] for row in result.all()]
            
            if not chat_ids:
                await message.reply(t("no_data", lang=lang))
                return
            
            response = f"📈 {t('stats_title', lang=lang)}\n\n"
            
            # Get stats for each chat
            for chat_id in chat_ids:
                # Get group stats
                stats = await stats_service.get_group_stats(chat_id)
                
                # Get chat name
                try:
                    chat = await message.bot.get_chat(chat_id)
                    chat_name = chat.title or f"Chat {chat_id}"
                except:
                    chat_name = f"Chat {chat_id}"
                
                response += f"💬 {chat_name}:\n"
                response += (
                    f"  {t('total_users', lang=lang)}: {stats['total_users']}\n"
                    f"  {t('total_posts', lang=lang)}: {stats['total_posts']}\n"
                    f"  {t('total_reactions', lang=lang)}: {stats['total_reactions']} "
                    f"({t('of_which_first_hour', lang=lang, count=stats['total_first_hour_reactions'])})\n"
                    f"  {t('per_week', lang=lang)}:\n"
                    f"    {t('posts', lang=lang)}: {stats['weekly_posts']}\n"
                    f"    {t('support', lang=lang)}: {stats['weekly_reactions']} "
                    f"({t('of_which_first_hour', lang=lang, count=stats['weekly_first_hour_reactions'])})\n\n"
                )
            
            await message.reply(response)
        else:
            # In groups, show stats for this group only
            settings = await user_service.get_or_create_settings(message.chat.id)
            lang = settings.language

            # Get group stats
            stats = await stats_service.get_group_stats(message.chat.id)

            # Format response
            response = (
                f"📈 {t('stats_title', lang=lang)}\n\n"
                f"{t('total_users', lang=lang)}: {stats['total_users']}\n"
                f"{t('total_posts', lang=lang)}: {stats['total_posts']}\n"
                f"{t('total_reactions', lang=lang)}: {stats['total_reactions']} "
                f"({t('of_which_first_hour', lang=lang, count=stats['total_first_hour_reactions'])})\n\n"
                f"{t('per_week', lang=lang)}:\n"
                f"{t('posts', lang=lang)}: {stats['weekly_posts']}\n"
                f"{t('support', lang=lang)}: {stats['weekly_reactions']} "
                f"({t('of_which_first_hour', lang=lang, count=stats['weekly_first_hour_reactions'])})"
            )

            await message.reply(response)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Show help message with available commands.

    Works only in private messages.

    Args:
        message: Incoming command message
    """
    if not message.chat:
        return

    # Only allow in private messages
    if message.chat.type != "private":
        return

    async with get_session() as session:
        lang = "ru"  # Default language for private messages
        await message.reply(t("help_text", lang=lang))
