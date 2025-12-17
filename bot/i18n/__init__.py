"""Internationalization (i18n) module for LinkedIn Karma Bot.

This module provides translation functionality for the bot,
supporting multiple languages (currently Russian and English).
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.i18n.ru import translations as ru_translations
from bot.i18n.en import translations as en_translations


# Available translations
TRANSLATIONS = {
    "ru": ru_translations,
    "en": en_translations,
}

# Default language
DEFAULT_LANGUAGE = "ru"


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Get a translated string for the given key and language.

    Args:
        key: Translation key to look up
        lang: Language code ('ru' or 'en'), defaults to 'ru'
        **kwargs: Optional keyword arguments for string formatting

    Returns:
        Translated string, or the key itself if translation is not found

    Examples:
        >>> t("welcome", lang="en")
        'Welcome to the group!...'

        >>> t("language_set", lang="ru", value="English")
        'Язык группы установлен: English'

    Notes:
        - If the language is not supported, falls back to default language
        - If the key is not found in translations, returns the key itself
        - Supports string formatting using {placeholders}
    """
    # Fallback to default language if not supported
    if lang not in TRANSLATIONS:
        lang = DEFAULT_LANGUAGE

    translations = TRANSLATIONS[lang]

    # Get the translation or fall back to the key itself
    text = translations.get(key, key)

    # Format the string with any provided kwargs
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            # If formatting fails, return the unformatted text
            pass

    return text


async def get_language(chat_id: int, session: AsyncSession) -> str:
    """Get the language setting for a specific chat.

    Args:
        chat_id: Telegram chat ID
        session: Async database session

    Returns:
        Language code for the chat ('ru' or 'en'), defaults to 'ru' if not set

    Example:
        >>> async with get_session() as session:
        ...     lang = await get_language(chat_id=-123456, session=session)
        ...     print(lang)
        'ru'
    """
    from bot.models import GroupSettings

    query = select(GroupSettings.language).where(
        GroupSettings.chat_id == chat_id
    )
    result = await session.execute(query)
    language = result.scalar_one_or_none()

    # Return the language if found, otherwise default
    return language if language in TRANSLATIONS else DEFAULT_LANGUAGE


__all__ = [
    "t",
    "get_language",
    "TRANSLATIONS",
    "DEFAULT_LANGUAGE",
]
