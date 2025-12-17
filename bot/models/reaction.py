"""
Reaction model for tracking user reactions to posts.
"""
from sqlalchemy import BigInteger, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if False:  # TYPE_CHECKING
    from .user import User
    from .post import Post


class Reaction(Base, TimestampMixin):
    """
    Represents a user's reaction to a post.

    A reaction is typically a thumbs-up or similar positive reaction
    that contributes to the author's karma.

    Attributes:
        id: Auto-incrementing primary key
        post_id: ID of the post being reacted to
        user_id: ID of the user giving the reaction
        created_at: When the reaction was created (from TimestampMixin)
    """

    __tablename__ = "reactions"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Auto-incrementing reaction ID"
    )

    # Foreign keys
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        doc="Post being reacted to"
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        doc="User giving the reaction"
    )

    # Relationships
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="reactions",
        doc="The post this reaction belongs to"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="reactions",
        doc="The user who gave this reaction"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "user_id",
            name="uq_reaction_post_user"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Reaction(id={self.id}, "
            f"post_id={self.post_id}, "
            f"user_id={self.user_id})>"
        )
