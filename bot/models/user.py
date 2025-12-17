"""
User model for storing Telegram user information and karma.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import BigInteger, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if False:  # TYPE_CHECKING
    from .post import Post
    from .reaction import Reaction
    from .user_karma import UserKarma


class User(Base):
    """
    Represents a Telegram user in the karma system.

    Attributes:
        telegram_id: Unique Telegram user ID (primary key)
        username: Telegram username (optional, can change)
        display_name: Display name (first name + last name)
        first_seen_at: When the user was first seen by the bot
        first_post_at: When the user made their first post (NULL for newcomers)
        karma_total: Total karma score accumulated by the user
    """

    __tablename__ = "users"

    # Primary key
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        doc="Telegram user ID"
    )

    # User information
    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Telegram username (without @)"
    )

    display_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="User's display name (first + last name)"
    )

    # Timestamps
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When the user was first seen"
    )

    first_post_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the user made their first post (NULL means newcomer)"
    )

    # Karma
    karma_total: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        doc="Total karma accumulated"
    )

    # Relationships
    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
        doc="Posts created by this user"
    )

    reactions: Mapped[List["Reaction"]] = relationship(
        "Reaction",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="Reactions given by this user"
    )

    karma_by_chat: Mapped[List["UserKarma"]] = relationship(
        "UserKarma",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="Karma records per chat/group"
    )

    def __repr__(self) -> str:
        return (
            f"<User(telegram_id={self.telegram_id}, "
            f"username={self.username}, "
            f"karma={self.karma_total})>"
        )

    @property
    def is_newcomer(self) -> bool:
        """Returns True if the user hasn't made their first post yet."""
        return self.first_post_at is None
