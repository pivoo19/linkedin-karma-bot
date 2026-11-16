"""Handlers module - exports all routers for registration."""

from aiogram import Router

from .messages import router as messages_router
from .reactions import router as reactions_router
from .commands import router as commands_router
from .admin import router as admin_router
from .topics import KarmaTopicFilter, router as topics_router

# In forum supergroups these routers handle messages only in enabled topics.
for _router in (admin_router, commands_router, messages_router):
    _router.message.filter(KarmaTopicFilter())


def get_routers() -> list[Router]:
    """Get all routers for registration.

    Returns:
        List of routers in order of registration
    """
    return [
        topics_router,     # /karma_on, /karma_off, /karma_topics (work in any topic)
        admin_router,      # Admin commands first
        commands_router,   # User commands
        reactions_router,  # Reaction handlers
        messages_router,   # Message handlers (should be last)
    ]


__all__ = [
    "get_routers",
    "messages_router",
    "reactions_router",
    "commands_router",
    "admin_router",
    "topics_router",
]
