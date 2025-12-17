"""
UserKarma model for storing user karma per group/chat.
"""
from sqlalchemy import BigInteger, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if False:  # TYPE_CHECKING
    from .user import User


class UserKarma(Base):
    """
    Represents a user's karma in a specific group/chat.

    Attributes:
        id: Auto-incrementing primary key
        user_id: Telegram user ID (foreign key to users)
        chat_id: Telegram chat ID
        karma_total: Total karma accumulated by the user in this chat
    """

    __tablename__ = "user_karma"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Auto-incrementing karma record ID"
    )

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        doc="Telegram user ID"
    )

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="Telegram chat ID"
    )

    # Karma
    karma_total: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        doc="Total karma accumulated in this chat"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="karma_by_chat",
        doc="The user this karma belongs to"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "chat_id",
            name="uq_user_karma_user_chat"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<UserKarma(id={self.id}, "
            f"user_id={self.user_id}, "
            f"chat_id={self.chat_id}, "
            f"karma_total={self.karma_total})>"
        )

