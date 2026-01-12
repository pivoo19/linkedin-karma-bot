# LinkedIn URL Entity Support Enhancement

## Summary

Enhanced the LinkedIn Karma Bot to detect and process LinkedIn URLs in Telegram messages, not only from plain text but also from Telegram message entities (clickable links and hyperlinked text).

## Changes Made

### 1. Enhanced LinkedIn Service (`bot/services/linkedin.py`)

Added new functions:
- `is_linkedin_url(url: str) -> bool` - Validates if a URL is a LinkedIn post URL
- `extract_linkedin_urls_from_message(message: Message) -> List[str]` - Extracts LinkedIn URLs from both:
  - Plain text content
  - Telegram message entities:
    - `url` type - Plain URLs that are auto-detected and made clickable
    - `text_link` type - Hyperlinked text where the URL is hidden behind display text

### 2. Updated Message Handler (`bot/handlers/messages.py`)

Modified the message handler to use the new `extract_linkedin_urls_from_message()` function instead of just parsing plain text, enabling detection of:
- Regular text URLs: `https://linkedin.com/posts/...`
- Clickable URLs (Telegram entities): When user pastes a URL and Telegram automatically makes it clickable
- Hyperlinked text: When text like "check this post" is hyperlinked to a LinkedIn URL

### 3. Comprehensive Test Coverage (`tests/test_linkedin.py`)

Added 16 new test cases covering:
- URL extraction from plain text
- URL extraction from `url` entities
- URL extraction from `text_link` entities
- Multiple entities in one message
- Deduplication of URLs
- Order preservation
- Handling of non-LinkedIn URLs in entities
- Edge cases (empty entities, non-URL entities, etc.)

## Benefits

1. **Better User Experience**: Users can now share LinkedIn posts in multiple ways:
   - Paste the URL directly
   - Let Telegram auto-format the URL
   - Use hyperlinked text (e.g., "my latest post" linking to LinkedIn)

2. **Backward Compatible**: All existing functionality is preserved - plain text URLs still work exactly as before

3. **Robust**: Handles edge cases like:
   - Multiple URLs in one message
   - Duplicate URLs from different sources
   - Non-LinkedIn URLs (properly ignored)
   - Mixed content (mentions, hashtags, etc.)

## Technical Details

### How Telegram Message Entities Work

When a user sends a message with URLs in Telegram, the platform can represent them in different ways:

1. **Plain text**: URL is just part of the text string
2. **URL entity**: Telegram detects the URL pattern and creates a clickable link
3. **Text link entity**: User explicitly creates a hyperlink where display text differs from the URL

Our enhancement detects all three cases, ensuring no LinkedIn post goes undetected.

## Testing

All 75 tests pass, including:
- 35 LinkedIn URL extraction tests (19 original + 16 new)
- 16 Karma service tests
- 24 Repository tests

To run tests:
```bash
python -m pytest tests/ -v
```

## Migration Notes

No database migrations required. This is a purely functional enhancement that doesn't affect data storage.

## Example Usage

```python
from aiogram.types import Message
from bot.services.linkedin import extract_linkedin_urls_from_message

# Works with any of these formats:
# 1. Plain text: "Check https://linkedin.com/posts/user-123"
# 2. Clickable URL entity: User pastes URL and Telegram makes it clickable
# 3. Hyperlinked text: "my post" with hidden URL behind it

urls = extract_linkedin_urls_from_message(message)
# Returns: ['https://linkedin.com/posts/user-123']
```
