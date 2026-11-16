"""Handlers module - exports all routers for registration."""

from aiogram import Router

from .messages import router as messages_router
from .reactions import router as reactions_router
from .commands import router as commands_router
from .admin import router as admin_router
from .topics import KarmaTopicFilter, router as topics_router

# In forum supergroups group messages are handled only in enabled topics.
# The filter sits on one parent router so the topic is checked once per message.
# New routers that handle group messages must be included into topic_gated_router.
topic_gated_router = Router(name="topic_gated")
topic_gated_router.message.filter(KarmaTopicFilter())
topic_gated_router.include_routers(
    admin_router,      # Admin commands first
    commands_router,   # User commands
    messages_router,   # Message handlers (should be last)
)


def get_routers() -> list[Router]:
    """Get all routers for registration.

    Returns:
        List of routers in order of registration
    """
    return [
        topics_router,       # /karma_on, /karma_off, /karma_topics (work in any topic)
        reactions_router,    # Reaction handlers (message_reaction, not gated)
        topic_gated_router,  # admin, commands, messages (gated by KarmaTopicFilter)
    ]


__all__ = [
    "get_routers",
    "messages_router",
    "reactions_router",
    "commands_router",
    "admin_router",
    "topics_router",
    "topic_gated_router",
]
