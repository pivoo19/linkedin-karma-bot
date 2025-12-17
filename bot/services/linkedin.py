"""LinkedIn URL parser service.

This module provides utilities for extracting and validating LinkedIn URLs
from text messages in the karma bot.
"""

import re
from typing import List


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
