"""Message handler for LinkedIn posts.

This module handles messages containing LinkedIn URLs and creates post records.
"""

from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import get_session
from bot.services.linkedin import extract_linkedin_urls
from bot.services.user import UserService
from bot.services.karma import KarmaService
from bot.database.repositories import UserKarmaRepository
from bot.i18n import t


router = Router(name="messages")


@router.message(F.text)
async def handle_message(message: Message):
    """Handle incoming messages with LinkedIn URLs.

    When a message contains a LinkedIn URL:
    1. Extract the LinkedIn URL
    2. Get or create user
    3. Create post record
    4. Update user's first_post_at if NULL
    5. Get user's karma stats
    6. Send formatted response with karma info

    Args:
        message: Incoming Telegram message
    """
    if not message.text or not message.from_user or not message.chat:
        return

    # Check if message contains LinkedIn URL
    linkedin_urls = extract_linkedin_urls(message.text)
    if not linkedin_urls:
        return

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
        stars = karma_service.karma_to_stars(weekly_karma)
        karma_display = f"{stars} ({weekly_karma})" if stars else f"({weekly_karma})"
        
        if is_newcomer:
            # Newcomer: "📝 @username 🌱 asks for support\nPer 7 days - Supported others: (0) | Asked for support: 1"
            response = t(
                "post_newcomer",
                lang=lang,
                username=username_display,
                karma=karma_display,
                posts=weekly_posts,
                period=settings.karma_period_days
            )
        elif is_veteran:
            # Veteran: "📝 @username 🎖️ (47) asks for support\nPer 7 days - Supported others: ⭐⭐ (4) | Asked for support: 1"
            karma_repo = UserKarmaRepository(session)
            total_karma = await karma_repo.get_total_karma(
                user_id=user.telegram_id,
                chat_id=message.chat.id
            )
            response = t(
                "post_veteran",
                lang=lang,
                username=username_display,
                total_karma=total_karma,
                karma=karma_display,
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
                posts=weekly_posts,
                period=settings.karma_period_days
            )

        # Send response
        await message.reply(response)
