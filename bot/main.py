"""Main bot entry point.

This module initializes and starts the LinkedIn Karma Bot.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import get_settings
from bot.database import init_db, close_db, init_engine
from bot.handlers import get_routers


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot."""
    # Load settings
    settings = get_settings()

    logger.info("Starting LinkedIn Karma Bot...")

    # Initialize database
    logger.info("Initializing database...")
    init_engine(settings.database_url)
    await init_db()
    logger.info("Database initialized successfully")

    # Create bot instance
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Create dispatcher
    dp = Dispatcher()

    # Register all routers
    routers = get_routers()
    for router in routers:
        dp.include_router(router)
        logger.info(f"Registered router: {router.name}")

    logger.info("All routers registered")

    try:
        # Start polling
        logger.info("Bot started. Polling for updates...")
        await dp.start_polling(bot)
    finally:
        # Cleanup
        logger.info("Shutting down bot...")
        await bot.session.close()
        await close_db()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
