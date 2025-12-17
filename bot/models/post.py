"""
Post model for storing LinkedIn posts shared in the chat.
"""
from typing import Optional, List

from sqlalchemy import BigInteger, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if False:  # TYPE_CHECKING
    from .user import User
    from .reaction import Reaction


class Post(Base, TimestampMixin):
    """
    Represents a LinkedIn post shared in a Telegram chat.

    Attributes:
        id: Auto-incrementing primary key
        message_id: Telegram message ID
        chat_id: Telegram chat ID where the post was shared
        author_id: ID of the user who shared the post
        linkedin_url: The LinkedIn URL that was shared
        created_at: When the post was created (from TimestampMixin)
    """

    __tablename__ = "posts"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Auto-incrementing post ID"
    )

    # Message identifiers
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="Telegram message ID"
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="Telegram chat ID"
    )

    # Author
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        doc="User who shared the post"
    )

    # Content
    linkedin_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="LinkedIn URL that was shared"
    )

    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="posts",
        doc="The user who shared this post"
    )

    reactions: Mapped[List["Reaction"]] = relationship(
        "Reaction",
        back_populates="post",
        cascade="all, delete-orphan",
        doc="Reactions to this post"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "chat_id",
            "message_id",
            name="uq_post_chat_message"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Post(id={self.id}, "
            f"chat_id={self.chat_id}, "
            f"message_id={self.message_id}, "
            f"author_id={self.author_id})>"
        )

    @property
    def reaction_count(self) -> int:
        """Returns the number of reactions this post has received."""
        return len(self.reactions) if self.reactions else 0
