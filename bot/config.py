from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram
    telegram_bot_token: str = Field(..., description="Telegram Bot API Token")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./karma_bot.db",
        description="Database connection URL"
    )

    # Default settings for new groups
    default_language: str = Field(default="ru", description="Default language (ru/en)")
    default_karma_period: int = Field(default=7, description="Default karma period in days")
    default_veteran_threshold: int = Field(default=30, description="Default veteran threshold")
    default_post_cost: int = Field(default=0, description="Default post cost in karma points")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
