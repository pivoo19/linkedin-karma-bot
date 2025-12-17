"""
Example usage of database models and repositories.

This file demonstrates how to use the database connection and repositories
in your bot code.
"""
import asyncio
from datetime import datetime

from bot.database import (
    init_engine,
    get_session,
    init_db,
    close_db,
    UserRepository,
    PostRepository,
    ReactionRepository,
    SettingsRepository,
)


async def main():
    """Example usage of the database."""

    # 1. Initialize database connection
    # For SQLite (development):
    init_engine("sqlite+aiosqlite:///./linkedin_karma.db", echo=True)

    # For PostgreSQL (production):
    # init_engine("postgresql+asyncpg://user:password@localhost/linkedin_karma", echo=False)

    # 2. Create all tables
    await init_db()
    print("Database initialized!")

    # 3. Use repositories
    async with get_session() as session:
        # Create repository instances
        user_repo = UserRepository(session)
        post_repo = PostRepository(session)
        reaction_repo = ReactionRepository(session)
        settings_repo = SettingsRepository(session)

        # Create or get a user
        user, created = await user_repo.get_or_create(
            telegram_id=123456789,
            username="john_doe",
            display_name="John Doe"
        )
        print(f"User: {user.username}, Created: {created}")

        # Get or create group settings
        settings, created = await settings_repo.get_or_create(chat_id=-1001234567890)
        print(f"Settings: language={settings.language}, Created: {created}")

        # Create a post
        post = await post_repo.create(
            message_id=42,
            chat_id=-1001234567890,
            author_id=123456789,
            linkedin_url="https://www.linkedin.com/posts/example"
        )
        print(f"Post created: ID={post.id}")

        # Set user's first post time if this is their first post
        if user.is_newcomer:
            await user_repo.set_first_post_time(
                telegram_id=user.telegram_id,
                post_time=post.created_at
            )
            print(f"Set first post time for {user.username}")

        # Add a reaction to the post
        reaction = await reaction_repo.add_reaction(
            post_id=post.id,
            user_id=987654321
        )
        if reaction:
            print(f"Reaction added: ID={reaction.id}")

        # Update user karma
        updated_user = await user_repo.update_karma_total(
            telegram_id=user.telegram_id,
            karma_delta=1  # +1 karma
        )
        print(f"User karma updated: {updated_user.karma_total}")

        # Get user posts in the last 7 days
        recent_posts = await post_repo.get_user_posts_in_period(
            user_id=user.telegram_id,
            days=7
        )
        print(f"User has {len(recent_posts)} posts in the last 7 days")

        # Count user reactions in the last 7 days
        reaction_count = await reaction_repo.count_user_reactions_in_period(
            user_id=987654321,
            days=7
        )
        print(f"User has {reaction_count} reactions in the last 7 days")

        # Update group settings
        updated_settings = await settings_repo.update(
            chat_id=settings.chat_id,
            language="en",
            karma_period_days=14
        )
        print(f"Settings updated: language={updated_settings.language}")

    # 4. Close database connection
    await close_db()
    print("Database closed!")


if __name__ == "__main__":
    asyncio.run(main())
