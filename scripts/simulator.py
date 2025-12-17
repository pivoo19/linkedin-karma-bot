#!/usr/bin/env python3
"""CLI simulator for testing LinkedIn Karma Bot without Telegram.

This script allows you to simulate bot operations directly from the command line,
useful for testing and development without needing a Telegram bot connection.

Usage:
    python scripts/simulator.py post <user_id> <username> <linkedin_url>
    python scripts/simulator.py react <user_id> <username> <post_id>
    python scripts/simulator.py unreact <user_id> <post_id>
    python scripts/simulator.py karma <user_id>
    python scripts/simulator.py top [limit]
    python scripts/simulator.py stats
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import bot modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from bot.config import get_settings
from bot.database.connection import close_db, get_session, init_db, init_engine
from bot.database.repositories import (
    PostRepository,
    ReactionRepository,
    SettingsRepository,
    UserRepository,
)
from bot.models import Post, User
from bot.services.karma import KarmaService
from bot.services.linkedin import is_linkedin_post


class BotSimulator:
    """Simulator for bot operations."""

    def __init__(self):
        """Initialize the simulator."""
        self.settings = get_settings()
        # Use SQLite by default for simulator
        if "postgresql" in self.settings.database_url:
            print("Warning: Using PostgreSQL database from config")
        init_engine(self.settings.database_url)

    async def setup(self):
        """Initialize database."""
        await init_db()
        print(f"Database initialized: {self.settings.database_url}")

    async def cleanup(self):
        """Cleanup database connection."""
        await close_db()

    async def post(self, user_id: int, username: str, linkedin_url: str):
        """Simulate posting a LinkedIn URL.

        Args:
            user_id: Telegram user ID
            username: Username
            linkedin_url: LinkedIn URL to post
        """
        if not is_linkedin_post(linkedin_url):
            print(f"Error: Invalid LinkedIn URL: {linkedin_url}")
            return

        async with get_session() as session:
            user_repo = UserRepository(session)
            post_repo = PostRepository(session)

            # Get or create user
            user, created = await user_repo.get_or_create(
                telegram_id=user_id, username=username, display_name=username
            )

            if created:
                print(f"Created new user: {username} (ID: {user_id})")
            else:
                print(f"Found existing user: {username} (ID: {user_id})")

            # Set first post time if newcomer
            if user.first_post_at is None:
                await user_repo.set_first_post_time(user_id, datetime.utcnow())
                print(f"  This is {username}'s first post!")

            # Create post (using dummy message_id and chat_id for simulator)
            post = await post_repo.create(
                message_id=hash(linkedin_url) % 1000000,  # Generate pseudo message ID
                chat_id=-1001234567890,  # Default chat ID
                author_id=user_id,
                linkedin_url=linkedin_url,
            )

            print(f"\nPost created successfully!")
            print(f"  Post ID: {post.id}")
            print(f"  Author: {username}")
            print(f"  URL: {linkedin_url}")
            print(f"  Created at: {post.created_at}")

    async def react(self, user_id: int, username: str, post_id: int):
        """Simulate adding a reaction to a post.

        Args:
            user_id: User ID who is reacting
            username: Username
            post_id: Post ID to react to
        """
        async with get_session() as session:
            user_repo = UserRepository(session)
            post_repo = PostRepository(session)
            reaction_repo = ReactionRepository(session)

            # Get or create user
            user, _ = await user_repo.get_or_create(
                telegram_id=user_id, username=username, display_name=username
            )

            # Get post
            post = await post_repo.get_by_id(post_id)
            if not post:
                print(f"Error: Post {post_id} not found")
                return

            # Check if reacting to own post
            if post.author_id == user_id:
                print("Error: Cannot react to your own post")
                return

            # Add reaction
            reaction = await reaction_repo.add_reaction(post_id, user_id)

            if reaction is None:
                print(f"Error: {username} has already reacted to post {post_id}")
                return

            # Update post author's karma
            await user_repo.update_karma_total(post.author_id, 1)

            # Get updated post author
            author = await user_repo.get_by_id(post.author_id)

            print(f"\nReaction added successfully!")
            print(f"  User: {username} reacted to post {post_id}")
            print(f"  Post author: {author.username} (new karma: {author.karma_total})")

    async def unreact(self, user_id: int, post_id: int):
        """Simulate removing a reaction from a post.

        Args:
            user_id: User ID who is unreacting
            post_id: Post ID to unreact from
        """
        async with get_session() as session:
            post_repo = PostRepository(session)
            reaction_repo = ReactionRepository(session)
            user_repo = UserRepository(session)

            # Get post
            post = await post_repo.get_by_id(post_id)
            if not post:
                print(f"Error: Post {post_id} not found")
                return

            # Remove reaction
            removed = await reaction_repo.remove_reaction(post_id, user_id)

            if not removed:
                print(f"Error: No reaction found for user {user_id} on post {post_id}")
                return

            # Update post author's karma
            await user_repo.update_karma_total(post.author_id, -1)

            # Get updated post author
            author = await user_repo.get_by_id(post.author_id)

            print(f"\nReaction removed successfully!")
            print(f"  User {user_id} unreacted from post {post_id}")
            print(f"  Post author: {author.username} (new karma: {author.karma_total})")

    async def karma(self, user_id: int):
        """Show karma information for a user.

        Args:
            user_id: User ID to check
        """
        async with get_session() as session:
            user_repo = UserRepository(session)
            karma_service = KarmaService(session)

            # Get user
            user = await user_repo.get_by_id(user_id)
            if not user:
                print(f"Error: User {user_id} not found")
                return

            # Get karma stats
            total_karma = user.karma_total
            is_newcomer = await karma_service.is_newcomer(user_id)
            is_veteran = await karma_service.is_veteran(user_id, threshold=30)
            stars = KarmaService.karma_to_stars(total_karma)

            print(f"\nKarma Stats for {user.username} (ID: {user_id})")
            print(f"  Total Karma: {total_karma} {stars}")
            print(f"  Status: {'Newcomer' if is_newcomer else 'Veteran' if is_veteran else 'Regular'}")
            print(f"  First seen: {user.first_seen_at}")
            print(f"  First post: {user.first_post_at if user.first_post_at else 'Never'}")

    async def top(self, limit: int = 10):
        """Show top users by karma.

        Args:
            limit: Number of top users to show
        """
        async with get_session() as session:
            result = await session.execute(
                select(User).order_by(User.karma_total.desc()).limit(limit)
            )
            users = result.scalars().all()

            if not users:
                print("No users found in database")
                return

            print(f"\nTop {limit} Users by Karma")
            print("-" * 60)
            for i, user in enumerate(users, 1):
                stars = KarmaService.karma_to_stars(user.karma_total)
                print(
                    f"{i:2d}. {user.username:20s} - {user.karma_total:4d} {stars}"
                )

    async def stats(self):
        """Show overall bot statistics."""
        async with get_session() as session:
            # Count users
            users_result = await session.execute(select(User))
            total_users = len(users_result.scalars().all())

            # Count posts
            posts_result = await session.execute(select(Post))
            posts = posts_result.scalars().all()
            total_posts = len(posts)

            # Count reactions
            from bot.models import Reaction

            reactions_result = await session.execute(select(Reaction))
            total_reactions = len(reactions_result.scalars().all())

            # Calculate average karma
            if total_users > 0:
                users_result = await session.execute(select(User))
                users = users_result.scalars().all()
                avg_karma = sum(u.karma_total for u in users) / total_users
            else:
                avg_karma = 0

            print("\nBot Statistics")
            print("-" * 60)
            print(f"  Total Users: {total_users}")
            print(f"  Total Posts: {total_posts}")
            print(f"  Total Reactions: {total_reactions}")
            print(f"  Average Karma: {avg_karma:.2f}")

            if total_posts > 0:
                print(
                    f"  Reactions per Post: {total_reactions / total_posts:.2f}"
                )


async def main():
    """Main entry point for the simulator."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Karma Bot CLI Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Post command
    post_parser = subparsers.add_parser("post", help="Simulate posting a LinkedIn URL")
    post_parser.add_argument("user_id", type=int, help="User ID")
    post_parser.add_argument("username", type=str, help="Username")
    post_parser.add_argument("linkedin_url", type=str, help="LinkedIn URL")

    # React command
    react_parser = subparsers.add_parser("react", help="Simulate reacting to a post")
    react_parser.add_argument("user_id", type=int, help="User ID")
    react_parser.add_argument("username", type=str, help="Username")
    react_parser.add_argument("post_id", type=int, help="Post ID to react to")

    # Unreact command
    unreact_parser = subparsers.add_parser(
        "unreact", help="Simulate removing a reaction"
    )
    unreact_parser.add_argument("user_id", type=int, help="User ID")
    unreact_parser.add_argument("post_id", type=int, help="Post ID to unreact from")

    # Karma command
    karma_parser = subparsers.add_parser("karma", help="Show user karma")
    karma_parser.add_argument("user_id", type=int, help="User ID")

    # Top command
    top_parser = subparsers.add_parser("top", help="Show top users")
    top_parser.add_argument(
        "limit", type=int, nargs="?", default=10, help="Number of users to show"
    )

    # Stats command
    subparsers.add_parser("stats", help="Show bot statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    simulator = BotSimulator()
    await simulator.setup()

    try:
        if args.command == "post":
            await simulator.post(args.user_id, args.username, args.linkedin_url)
        elif args.command == "react":
            await simulator.react(args.user_id, args.username, args.post_id)
        elif args.command == "unreact":
            await simulator.unreact(args.user_id, args.post_id)
        elif args.command == "karma":
            await simulator.karma(args.user_id)
        elif args.command == "top":
            await simulator.top(args.limit)
        elif args.command == "stats":
            await simulator.stats()
    finally:
        await simulator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
