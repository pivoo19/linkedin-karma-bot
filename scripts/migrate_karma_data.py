"""Script to migrate karma data from users.karma_total to user_karma table.

This script:
1. Finds all unique (user_id, chat_id) combinations from posts and reactions
2. Calculates karma for each user in each chat (unique posts they reacted to)
3. Creates user_karma records
"""
import asyncio
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.database import get_session, init_engine, close_db
from bot.models import User, Post, Reaction, UserKarma
from bot.database.repositories import UserKarmaRepository


async def migrate_karma_data():
    """Migrate karma data from users.karma_total to user_karma table."""
    # Initialize database connection
    settings = get_settings()
    init_engine(settings.database_url)
    
    try:
        async with get_session() as session:
            print("🔄 Starting karma data migration...")
            
            # Get all unique (user_id, chat_id) combinations from reactions
            # This represents users who have given reactions in specific chats
            reactions_query = (
                select(
                    Reaction.user_id,
                    Post.chat_id,
                    func.count(func.distinct(Reaction.post_id)).label('karma')
                )
                .join(Post, Reaction.post_id == Post.id)
                .group_by(Reaction.user_id, Post.chat_id)
            )
            
            result = await session.execute(reactions_query)
            reaction_data = result.all()
            
            print(f"📊 Found {len(reaction_data)} user-chat combinations from reactions")
            
            karma_repo = UserKarmaRepository(session)
            migrated_count = 0
            
            for user_id, chat_id, karma in reaction_data:
                # Get or create user_karma record
                user_karma, created = await karma_repo.get_or_create(
                    user_id=user_id,
                    chat_id=chat_id
                )
                
                # Update karma if it's different
                if user_karma.karma_total != karma:
                    user_karma.karma_total = karma
                    await session.commit()
                    await session.refresh(user_karma)
                    migrated_count += 1
                    print(f"  ✅ User {user_id} in chat {chat_id}: {karma} karma")
            
            # Also create records for users who posted but never reacted
            # (they should have 0 karma, but we need the record)
            posts_query = (
                select(
                    Post.author_id,
                    Post.chat_id
                )
                .distinct()
            )
            
            result = await session.execute(posts_query)
            post_data = result.all()
            
            print(f"📊 Found {len(post_data)} user-chat combinations from posts")
            
            for user_id, chat_id in post_data:
                user_karma, created = await karma_repo.get_or_create(
                    user_id=user_id,
                    chat_id=chat_id
                )
                if created:
                    print(f"  ✅ Created record for user {user_id} in chat {chat_id} (0 karma)")
            
            await session.commit()
            
            print(f"\n✨ Migration completed!")
            print(f"   Migrated {migrated_count} karma records")
            print(f"   Total user-chat combinations: {len(reaction_data) + len(post_data)}")
    finally:
        # Close database connection
        await close_db()


if __name__ == "__main__":
    asyncio.run(migrate_karma_data())

