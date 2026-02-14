"""Message handler for LinkedIn posts.

This module handles messages containing LinkedIn URLs and creates post records.
"""

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import get_session
from bot.services.linkedin import extract_linkedin_urls_from_message
from bot.services.user import UserService
from bot.services.karma import KarmaService
from bot.database.repositories import UserKarmaRepository
from bot.i18n import t


router = Router(name="messages")
logger = logging.getLogger(__name__)


def get_message_link(message: Message) -> str:
    """Generate a link to the message in the chat.
    
    Args:
        message: Telegram message object
        
    Returns:
        Link to the message in format https://t.me/... or https://t.me/c/...
    """
    if not message.chat:
        return ""
    
    chat_id = message.chat.id
    message_id = message.message_id
    
    # If chat has username, use public link format
    if message.chat.username:
        return f"https://t.me/{message.chat.username}/{message_id}"
    
    # For private chats/channels, use c/ format
    if chat_id < 0:
        # For supergroups and channels (chat_id starts with -100)
        # Format: https://t.me/c/{abs(chat_id) - 1000000000000}/{message_id}
        if abs(chat_id) >= 1000000000000:
            # Supergroup or channel
            private_chat_id = abs(chat_id) - 1000000000000
            return f"https://t.me/c/{private_chat_id}/{message_id}"
        else:
            # Regular group (rare case)
            return f"https://t.me/c/{abs(chat_id)}/{message_id}"
    
    # For private chats (positive chat_id, very rare for groups)
    return f"https://t.me/c/{chat_id}/{message_id}"


async def get_chat_users(session: AsyncSession, chat_id: int) -> list[int]:
    """Get list of all user IDs who have interacted with the chat (posted or reacted).
    
    Args:
        session: Database session
        chat_id: Telegram chat ID
        
    Returns:
        List of user IDs who have interacted with the chat
    """
    try:
        from sqlalchemy import select
        from bot.models import Post, Reaction

        # Get all user IDs from posts
        post_users_query = select(Post.author_id).where(
            Post.chat_id == chat_id
        ).distinct()
        
        # Get all user IDs from reactions (through posts in this chat)
        reaction_users_query = (
            select(Reaction.user_id)
            .join(Post, Reaction.post_id == Post.id)
            .where(Post.chat_id == chat_id)
            .distinct()
        )
        
        # Execute both queries and combine results
        post_users_result = await session.execute(post_users_query)
        post_user_ids = set(post_users_result.scalars().all())
        
        reaction_users_result = await session.execute(reaction_users_query)
        reaction_user_ids = set(reaction_users_result.scalars().all())
        
        # Union of both sets
        all_user_ids = list(post_user_ids | reaction_user_ids)
        
        return all_user_ids
    except Exception as e:
        logger.error(f"Error getting chat users: {e}", exc_info=True)
        return []


async def notify_users(
    bot,
    session: AsyncSession,
    chat_id: int,
    response_text: str,
    message_link: str,
    lang: str,
    chat_title: str | None = None,
) -> None:
    """Send notification to all chat users about a new LinkedIn post.
    
    Args:
        bot: Bot instance
        session: Database session
        chat_id: Telegram chat ID
        response_text: The response text that was sent to the group
        message_link: Link to the message in the group
        lang: Language code for the notification
        chat_title: Optional group title to include in personal notification
    """
    try:
        user_ids = await get_chat_users(session, chat_id)
        if not user_ids:
            return

        group_name_block = ""
        if chat_title:
            group_name_block = t(
                "group_name_block",
                lang=lang,
                title=chat_title
            )

        notification_text = t(
            "user_notification",
            lang=lang,
            response=response_text,
            message_link=message_link,
            group_name_block=group_name_block,
        )

        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=notification_text
                )
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error sending notification to user {user_id}: {error_msg}")
    except Exception as e:
        logger.error(f"Error in notify_users: {e}", exc_info=True)


@router.message(F.text)
async def handle_message(message: Message):
    """Handle incoming messages with LinkedIn URLs.

    When a message contains a LinkedIn URL:
    1. Extract the LinkedIn URL from text and message entities
    2. Get or create user
    3. Create post record
    4. Update user's first_post_at if NULL
    5. Get user's karma stats
    6. Send formatted response with karma info

    Args:
        message: Incoming Telegram message
    """
    if not message.from_user or not message.chat:
        return

    # Check if message contains LinkedIn URL (from text or entities)
    linkedin_urls = extract_linkedin_urls_from_message(message)
    if not linkedin_urls:
        return
    
    logger.info(
        f"LinkedIn URL detected from user {message.from_user.id} in chat {message.chat.id}: {linkedin_urls[0]}"
    )

    # Get first LinkedIn URL
    linkedin_url = linkedin_urls[0]

    # Get database session
    async with get_session() as session:
        user_service = UserService(session)
        karma_service = KarmaService(session)

        # Get or create user
        user = await user_service.get_or_create_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

        # Get group settings
        settings = await user_service.get_or_create_settings(message.chat.id)
        lang = settings.language

        # Check post cost (if set)
        if settings.post_cost > 0:
            karma_repo = UserKarmaRepository(session)
            user_karma = await karma_repo.get_total_karma(
                user_id=user.telegram_id,
                chat_id=message.chat.id
            )
            if user_karma < settings.post_cost:
                await message.reply(
                    t("not_enough_karma", lang=lang,
                      required=settings.post_cost,
                      current=user_karma)
                )
                return  # Don't create post

        # Check if this is the first post (BEFORE creating the post)
        is_newcomer = user.first_post_at is None

        # Create post record
        await user_service.create_post(
            user_id=user.telegram_id,
            message_id=message.message_id,
            chat_id=message.chat.id,
            linkedin_url=linkedin_url
        )

        # Update first_post_at if NULL (after creating post)
        if is_newcomer:
            user.first_post_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)

        # Get user's karma stats
        weekly_karma = await karma_service.get_weekly_karma(
            user_id=user.telegram_id,
            chat_id=message.chat.id,
            period_days=settings.karma_period_days
        )

        weekly_posts = await karma_service.get_weekly_posts_count(
            user_id=user.telegram_id,
            chat_id=message.chat.id,
            period_days=settings.karma_period_days
        )
        weekly_first_hour = await karma_service.get_weekly_first_hour_karma(
            user_id=user.telegram_id,
            chat_id=message.chat.id,
            period_days=settings.karma_period_days
        )

        # Check veteran status
        is_veteran = await karma_service.is_veteran(
            user.telegram_id,
            chat_id=message.chat.id,
            threshold=settings.veteran_threshold
        )

        # Format username for display
        username_display = f"@{user.username}" if user.username else (
            user.display_name or "User"
        )

        # Format response message based on user status using i18n
        # Format: "Per 7 days - Supported others: ⭐ (X) | Asked for support: Y"
        karma_display = str(weekly_karma)
        karma_repo = UserKarmaRepository(session)
        total_karma = await karma_repo.get_total_karma(
            user_id=user.telegram_id,
            chat_id=message.chat.id
        )
        all_time_display = t(
            "supported_all_time",
            lang=lang,
            count=total_karma
        )
        
        if is_newcomer:
            # Newcomer: "📝 @username 🌱 asks for support\nPer 7 days - Supported others: (0) | Asked for support: 1"
            response = t(
                "post_newcomer",
                lang=lang,
                username=username_display,
                karma=karma_display,
                all_time=all_time_display,
                first_hour=weekly_first_hour,
                posts=weekly_posts,
                period=settings.karma_period_days
            )
        elif is_veteran:
            # Veteran: "📝 @username 🎖️ (47) asks for support\nPer 7 days - Supported others: ⭐⭐ (4) | Asked for support: 1"
            response = t(
                "post_veteran",
                lang=lang,
                username=username_display,
                karma=karma_display,
                all_time=all_time_display,
                first_hour=weekly_first_hour,
                posts=weekly_posts,
                period=settings.karma_period_days
            )
        else:
            # Regular: "📝 @username asks for support\nPer 7 days - Supported others: ⭐⭐⭐ (8) | Asked for support: 2"
            response = t(
                "post_regular",
                lang=lang,
                username=username_display,
                karma=karma_display,
                all_time=all_time_display,
                first_hour=weekly_first_hour,
                posts=weekly_posts,
                period=settings.karma_period_days
            )

        await message.reply(response)
        try:
            message_link = get_message_link(message)
            await notify_users(
                bot=message.bot,
                session=session,
                chat_id=message.chat.id,
                response_text=response,
                message_link=message_link,
                lang=lang,
                chat_title=getattr(message.chat, "title", None),
            )
        except Exception as e:
            logger.error(f"Error in notification process: {e}", exc_info=True)
