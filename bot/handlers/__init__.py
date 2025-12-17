"""Handlers module - exports all routers for registration."""

from aiogram import Router

from .messages import router as messages_router
from .reactions import router as reactions_router
from .commands import router as commands_router
from .admin import router as admin_router


def get_routers() -> list[Router]:
    """Get all routers for registration.

    Returns:
        List of routers in order of registration
    """
    return [
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
]
