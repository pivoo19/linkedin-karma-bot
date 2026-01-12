"""LinkedIn URL parser service.

This module provides utilities for extracting and validating LinkedIn URLs
from text messages in the karma bot.
"""

import re
from typing import List, Optional
from aiogram.types import Message, MessageEntity


# Regex pattern to match LinkedIn post URLs
# Matches the following patterns:
# - linkedin.com/posts/...
# - linkedin.com/feed/update/...
# - linkedin.com/pulse/...
LINKEDIN_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/'
    r'(?:posts/[^\s]+|feed/update/[^\s]+|pulse/[^\s]+)',
    re.IGNORECASE
)


def is_linkedin_url(url: str) -> bool:
    """Check if a URL is a valid LinkedIn post URL.

    Args:
        url: The URL to check

    Returns:
        True if the URL is a LinkedIn post URL, False otherwise
    """
    if not url:
        return False
    return bool(LINKEDIN_PATTERN.match(url))


def extract_linkedin_urls(text: str) -> List[str]:
    """Extract all LinkedIn post URLs from the given text.

    Args:
        text: The text to search for LinkedIn URLs

    Returns:
        A list of unique LinkedIn URLs found in the text

    Examples:
        >>> extract_linkedin_urls("Check out https://linkedin.com/posts/user-123/")
        ['https://linkedin.com/posts/user-123/']

        >>> extract_linkedin_urls("Multiple links: https://linkedin.com/posts/abc https://linkedin.com/pulse/xyz")
        ['https://linkedin.com/posts/abc', 'https://linkedin.com/pulse/xyz']
    """
    if not text:
        return []

    # Find all matches and return unique URLs
    matches = LINKEDIN_PATTERN.findall(text)
    return list(set(matches))  # Remove duplicates


def extract_linkedin_urls_from_message(message: Message) -> List[str]:
    """Extract all LinkedIn post URLs from a Telegram message.
    
    This function extracts URLs from both:
    1. Plain text in the message
    2. Telegram message entities (url, text_link types)
    
    Args:
        message: Telegram message object
        
    Returns:
        A list of unique LinkedIn URLs found in the message
    """
    linkedin_urls = []
    
    # Extract from plain text
    if message.text:
        linkedin_urls.extend(extract_linkedin_urls(message.text))
    
    # Extract from message entities
    if message.entities:
        for entity in message.entities:
            url = None
            
            # Handle 'url' type entities (plain URLs in text)
            if entity.type == "url" and message.text:
                url = message.text[entity.offset:entity.offset + entity.length]
            
            # Handle 'text_link' type entities (hyperlinked text)
            elif entity.type == "text_link" and entity.url:
                url = entity.url
            
            # Check if extracted URL is a LinkedIn URL
            if url and is_linkedin_url(url):
                linkedin_urls.append(url)
    
    # Return unique URLs while preserving order
    seen = set()
    unique_urls = []
    for url in linkedin_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls


def is_linkedin_post(text: str) -> bool:
    """Check if the text contains at least one LinkedIn post URL.

    Args:
        text: The text to check for LinkedIn URLs

    Returns:
        True if the text contains at least one LinkedIn URL, False otherwise

    Examples:
        >>> is_linkedin_post("https://linkedin.com/posts/user-123/")
        True

        >>> is_linkedin_post("Just a regular message")
        False
    """
    if not text:
        return False

    return bool(LINKEDIN_PATTERN.search(text))
