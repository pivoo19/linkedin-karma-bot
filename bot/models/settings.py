"""
Group settings model for chat-specific configuration.
"""
from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class GroupSettings(Base):
    """
    Stores configuration settings for a Telegram group chat.

    Attributes:
        chat_id: Telegram chat ID (primary key)
        language: Language code (e.g., 'ru', 'en')
        karma_period_days: Number of days to count for karma period
        veteran_threshold: Days after first post to be considered veteran
        post_cost: Karma cost to post (0 means free posting)
    """

    __tablename__ = "group_settings"

    # Primary key
    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        doc="Telegram chat ID"
    )

    # Settings
    language: Mapped[str] = mapped_column(
        String(2),
        default="ru",
        server_default="ru",
        nullable=False,
        doc="Language code (ISO 639-1)"
    )

    karma_period_days: Mapped[int] = mapped_column(
        Integer,
        default=7,
        server_default="7",
        nullable=False,
        doc="Number of days for karma calculation period"
    )

    veteran_threshold: Mapped[int] = mapped_column(
        Integer,
        default=30,
        server_default="30",
        nullable=False,
        doc="Days after first post to be considered a veteran"
    )

    post_cost: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        doc="Karma cost to post (0 = free posting)"
    )

    def __repr__(self) -> str:
        return (
            f"<GroupSettings(chat_id={self.chat_id}, "
            f"language={self.language}, "
            f"karma_period_days={self.karma_period_days})>"
        )
