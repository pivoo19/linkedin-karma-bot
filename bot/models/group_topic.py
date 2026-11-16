"""
Group topic model: forum topics where the karma bot is enabled.
"""
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class GroupTopic(Base, TimestampMixin):
    """
    A forum topic where the bot is enabled.

    In forum supergroups the bot works only in topics listed here.

    Attributes:
        chat_id: Telegram chat ID of the forum supergroup
        topic_id: Forum topic ID (message_thread_id); 1 means the General topic
    """

    __tablename__ = "group_topics"

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        doc="Telegram chat ID"
    )

    topic_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        doc="Forum topic ID (1 = General)"
    )

    def __repr__(self) -> str:
        return f"<GroupTopic(chat_id={self.chat_id}, topic_id={self.topic_id})>"
