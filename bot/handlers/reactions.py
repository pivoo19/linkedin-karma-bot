"""Reaction handler for message reactions.

This module handles message_reaction updates and manages karma based on reactions.
"""

from aiogram import Router
from aiogram.types import MessageReactionUpdated, ReactionTypeEmoji
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import get_session
from bot.models import Reaction, User, Post
from bot.services.user import UserService
from bot.database.repositories import UserKarmaRepository


router = Router(name="reactions")


@router.message_reaction()
async def handle_reaction(reaction_update: MessageReactionUpdated):
    """Handle message reaction updates.

    On reaction added:
    - Check if message is a LinkedIn post
    - Check it's not self-reaction
    - Add reaction to DB (ignore if duplicate)
    - Increment reactor's karma_total (user who gave the reaction)

    On reaction removed:
    - Remove reaction from DB
    - Decrement reactor's karma_total (user who removed the reaction)

    Args:
        reaction_update: Reaction update event
    """
    if not reaction_update.user or not reaction_update.chat:
        return

    async with get_session() as session:
        user_service = UserService(session)

        # Get the post by message ID
        post = await user_service.get_post_by_message(
            chat_id=reaction_update.chat.id,
            message_id=reaction_update.message_id
        )

        if not post:
            # Not a LinkedIn post, ignore
            return

        # Check if it's a self-reaction
        if reaction_update.user.id == post.author_id:
            # Self-reaction, ignore
            return

        # Get or create reactor user
        reactor = await user_service.get_or_create_user(
            user_id=reaction_update.user.id,
            username=reaction_update.user.username,
            first_name=reaction_update.user.first_name,
            last_name=reaction_update.user.last_name
        )

        # Check if reactions were added or removed
        old_reactions = set()
        new_reactions = set()

        for reaction in reaction_update.old_reaction:
            if isinstance(reaction, ReactionTypeEmoji):
                old_reactions.add(reaction.emoji)

        for reaction in reaction_update.new_reaction:
            if isinstance(reaction, ReactionTypeEmoji):
                new_reactions.add(reaction.emoji)

        # Reactions added
        added_reactions = new_reactions - old_reactions
        # Reactions removed
        removed_reactions = old_reactions - new_reactions

        # Handle added reactions
        if added_reactions:
            # Check if reaction already exists
            result = await session.execute(
                select(Reaction).where(
                    Reaction.post_id == post.id,
                    Reaction.user_id == reactor.telegram_id
                )
            )
            existing_reaction = result.scalar_one_or_none()

            if not existing_reaction:
                # Create new reaction
                new_reaction = Reaction(
                    post_id=post.id,
                    user_id=reactor.telegram_id
                )
                session.add(new_reaction)

                # Increment reactor's karma in this chat (user who gave the reaction)
                # This counts unique posts the user supported
                karma_repo = UserKarmaRepository(session)
                await karma_repo.update_karma_total(
                    user_id=reactor.telegram_id,
                    chat_id=reaction_update.chat.id,
                    karma_delta=1
                )

                await session.commit()

        # Handle removed reactions
        if removed_reactions:
            # Find and delete reaction
            result = await session.execute(
                select(Reaction).where(
                    Reaction.post_id == post.id,
                    Reaction.user_id == reactor.telegram_id
                )
            )
            existing_reaction = result.scalar_one_or_none()

            if existing_reaction:
                # Delete reaction
                await session.delete(existing_reaction)

                # Decrement reactor's karma in this chat (don't go below 0)
                karma_repo = UserKarmaRepository(session)
                current_karma = await karma_repo.get_total_karma(
                    user_id=reactor.telegram_id,
                    chat_id=reaction_update.chat.id
                )
                if current_karma > 0:
                    await karma_repo.update_karma_total(
                        user_id=reactor.telegram_id,
                        chat_id=reaction_update.chat.id,
                        karma_delta=-1
                    )

                await session.commit()
