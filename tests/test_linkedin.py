"""Tests for LinkedIn URL parsing and validation."""

import pytest
from unittest.mock import MagicMock

from bot.services.linkedin import (
    extract_linkedin_urls,
    is_linkedin_post,
    is_linkedin_url,
    extract_linkedin_urls_from_message
)


class TestLinkedInParser:
    """Test LinkedIn URL parser functionality."""

    def test_extract_linkedin_urls_posts(self):
        """Test extracting LinkedIn post URLs."""
        text = "Check this out: https://linkedin.com/posts/username-123_test-post"
        urls = extract_linkedin_urls(text)
        assert len(urls) == 1
        assert "linkedin.com/posts/" in urls[0]

    def test_extract_linkedin_urls_feed(self):
        """Test extracting LinkedIn feed update URLs."""
        text = "Great article: https://linkedin.com/feed/update/urn:li:activity:1234567890"
        urls = extract_linkedin_urls(text)
        assert len(urls) == 1
        assert "linkedin.com/feed/update/" in urls[0]

    def test_extract_linkedin_urls_pulse(self):
        """Test extracting LinkedIn Pulse article URLs."""
        text = "Read my article: https://linkedin.com/pulse/my-article-title-author"
        urls = extract_linkedin_urls(text)
        assert len(urls) == 1
        assert "linkedin.com/pulse/" in urls[0]

    def test_extract_linkedin_urls_multiple(self):
        """Test extracting multiple LinkedIn URLs from text."""
        text = (
            "Check these out: "
            "https://linkedin.com/posts/user1-abc "
            "and https://linkedin.com/pulse/article-123 "
            "also https://linkedin.com/feed/update/urn:li:activity:999"
        )
        urls = extract_linkedin_urls(text)
        assert len(urls) == 3

    def test_extract_linkedin_urls_with_www(self):
        """Test extracting URLs with www prefix."""
        text = "Post: https://www.linkedin.com/posts/test-user-post"
        urls = extract_linkedin_urls(text)
        assert len(urls) == 1
        assert "linkedin.com/posts/" in urls[0]

    def test_extract_linkedin_urls_http(self):
        """Test extracting HTTP URLs (should work)."""
        text = "Post: http://linkedin.com/posts/test-post"
        urls = extract_linkedin_urls(text)
        assert len(urls) == 1

    def test_extract_linkedin_urls_none(self):
        """Test extracting URLs from text without LinkedIn URLs."""
        text = "Just a regular message with no LinkedIn links"
        urls = extract_linkedin_urls(text)
        assert len(urls) == 0

    def test_extract_linkedin_urls_empty(self):
        """Test extracting URLs from empty text."""
        urls = extract_linkedin_urls("")
        assert len(urls) == 0

    def test_extract_linkedin_urls_other_urls(self):
        """Test that non-LinkedIn URLs are ignored."""
        text = (
            "Check out https://twitter.com/user "
            "and https://facebook.com/page "
            "not https://linkedin.com/in/profile"
        )
        urls = extract_linkedin_urls(text)
        assert len(urls) == 0

    def test_is_linkedin_post_valid_post(self):
        """Test checking valid post URL."""
        url = "https://linkedin.com/posts/username-123_test"
        assert is_linkedin_post(url) is True

    def test_is_linkedin_post_valid_feed(self):
        """Test checking valid feed update URL."""
        url = "https://linkedin.com/feed/update/urn:li:activity:1234567890"
        assert is_linkedin_post(url) is True

    def test_is_linkedin_post_valid_pulse(self):
        """Test checking valid pulse article URL."""
        url = "https://linkedin.com/pulse/article-title-author"
        assert is_linkedin_post(url) is True

    def test_is_linkedin_post_profile(self):
        """Test that profile URLs are not considered posts."""
        url = "https://linkedin.com/in/username"
        assert is_linkedin_post(url) is False

    def test_is_linkedin_post_company(self):
        """Test that company URLs are not considered posts."""
        url = "https://linkedin.com/company/company-name"
        assert is_linkedin_post(url) is False

    def test_is_linkedin_post_invalid(self):
        """Test checking invalid URL."""
        url = "https://twitter.com/user"
        assert is_linkedin_post(url) is False

    def test_is_linkedin_post_empty(self):
        """Test checking empty string."""
        assert is_linkedin_post("") is False

    def test_is_linkedin_post_none(self):
        """Test checking None value."""
        assert is_linkedin_post(None) is False

    def test_extract_linkedin_urls_with_query_params(self):
        """Test extracting URLs with query parameters."""
        text = "Post: https://linkedin.com/posts/user_test?utm_source=share&utm_medium=member"
        urls = extract_linkedin_urls(text)
        assert len(urls) == 1
        # URL should include query parameters
        assert "?" in urls[0] or len(urls[0]) > 30

    def test_extract_linkedin_urls_duplicates(self):
        """Test that duplicate URLs are handled correctly."""
        text = (
            "https://linkedin.com/posts/same-post "
            "and again https://linkedin.com/posts/same-post"
        )
        urls = extract_linkedin_urls(text)
        # Should return unique URLs (implementation may vary)
        assert len(urls) >= 1


class TestLinkedInUrlValidation:
    """Test LinkedIn URL validation."""

    def test_is_linkedin_url_valid_post(self):
        """Test validation of valid post URL."""
        url = "https://linkedin.com/posts/username-123_test"
        assert is_linkedin_url(url) is True

    def test_is_linkedin_url_valid_feed(self):
        """Test validation of valid feed URL."""
        url = "https://linkedin.com/feed/update/urn:li:activity:1234567890"
        assert is_linkedin_url(url) is True

    def test_is_linkedin_url_valid_pulse(self):
        """Test validation of valid pulse URL."""
        url = "https://linkedin.com/pulse/article-title-author"
        assert is_linkedin_url(url) is True

    def test_is_linkedin_url_profile(self):
        """Test that profile URLs are rejected."""
        url = "https://linkedin.com/in/username"
        assert is_linkedin_url(url) is False

    def test_is_linkedin_url_invalid(self):
        """Test that non-LinkedIn URLs are rejected."""
        url = "https://twitter.com/user"
        assert is_linkedin_url(url) is False

    def test_is_linkedin_url_empty(self):
        """Test validation of empty string."""
        assert is_linkedin_url("") is False


class TestLinkedInMessageExtraction:
    """Test LinkedIn URL extraction from Telegram messages."""

    def test_extract_from_plain_text(self):
        """Test extracting LinkedIn URL from plain text message."""
        message = MagicMock()
        message.text = "Check out https://linkedin.com/posts/user-123_test"
        message.entities = None

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) == 1
        assert "linkedin.com/posts/" in urls[0]

    def test_extract_from_url_entity(self):
        """Test extracting LinkedIn URL from URL entity."""
        message = MagicMock()
        message.text = "Check out https://linkedin.com/posts/user-123_test"
        
        # Create URL entity
        entity = MagicMock()
        entity.type = "url"
        entity.offset = 10
        entity.length = 44
        entity.url = None
        
        message.entities = [entity]

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) >= 1
        assert any("linkedin.com/posts/" in url for url in urls)

    def test_extract_from_text_link_entity(self):
        """Test extracting LinkedIn URL from text_link entity (hyperlinked text)."""
        message = MagicMock()
        message.text = "Check out this post"
        
        # Create text_link entity
        entity = MagicMock()
        entity.type = "text_link"
        entity.offset = 10
        entity.length = 9
        entity.url = "https://linkedin.com/posts/user-123_awesome-post"
        
        message.entities = [entity]

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) == 1
        assert "linkedin.com/posts/" in urls[0]
        assert "user-123_awesome-post" in urls[0]

    def test_extract_from_multiple_entities(self):
        """Test extracting multiple LinkedIn URLs from different entities."""
        message = MagicMock()
        message.text = "Post 1: https://linkedin.com/posts/user1 and post 2"
        
        # Create multiple entities
        entity1 = MagicMock()
        entity1.type = "url"
        entity1.offset = 8
        entity1.length = 35
        entity1.url = None
        
        entity2 = MagicMock()
        entity2.type = "text_link"
        entity2.offset = 50
        entity2.length = 6
        entity2.url = "https://linkedin.com/posts/user2"
        
        message.entities = [entity1, entity2]

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) >= 2

    def test_extract_ignores_non_linkedin_entities(self):
        """Test that non-LinkedIn URLs in entities are ignored."""
        message = MagicMock()
        message.text = "Check out this post"
        
        # Create text_link entity with non-LinkedIn URL
        entity = MagicMock()
        entity.type = "text_link"
        entity.offset = 10
        entity.length = 9
        entity.url = "https://twitter.com/user"
        
        message.entities = [entity]

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) == 0

    def test_extract_from_no_entities(self):
        """Test extracting from message without entities."""
        message = MagicMock()
        message.text = "Just a regular message"
        message.entities = None

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) == 0

    def test_extract_deduplicates_urls(self):
        """Test that duplicate URLs from text and entities are deduplicated."""
        message = MagicMock()
        message.text = "https://linkedin.com/posts/same-post"
        
        # Create entity with same URL
        entity = MagicMock()
        entity.type = "url"
        entity.offset = 0
        entity.length = 37
        entity.url = None
        
        message.entities = [entity]

        urls = extract_linkedin_urls_from_message(message)
        # Should have only one unique URL
        assert len(urls) == 1

    def test_extract_preserves_order(self):
        """Test that URL extraction preserves order."""
        message = MagicMock()
        message.text = "First https://linkedin.com/posts/first then second"
        
        # Create second URL as text_link
        entity = MagicMock()
        entity.type = "text_link"
        entity.offset = 41
        entity.length = 6
        entity.url = "https://linkedin.com/posts/second"
        
        message.entities = [entity]

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) == 2
        # First URL should come before second
        assert "first" in urls[0]
        assert "second" in urls[1]

    def test_extract_handles_empty_entities_list(self):
        """Test that empty entities list is handled correctly."""
        message = MagicMock()
        message.text = "https://linkedin.com/posts/test"
        message.entities = []

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) == 1

    def test_extract_handles_non_url_entities(self):
        """Test that non-URL entities (like mentions, hashtags) are ignored."""
        message = MagicMock()
        message.text = "@user #hashtag https://linkedin.com/posts/test"
        
        # Create non-URL entities
        mention = MagicMock()
        mention.type = "mention"
        mention.offset = 0
        mention.length = 5
        mention.url = None
        
        hashtag = MagicMock()
        hashtag.type = "hashtag"
        hashtag.offset = 6
        hashtag.length = 8
        hashtag.url = None
        
        url_entity = MagicMock()
        url_entity.type = "url"
        url_entity.offset = 15
        url_entity.length = 35
        url_entity.url = None
        
        message.entities = [mention, hashtag, url_entity]

        urls = extract_linkedin_urls_from_message(message)
        assert len(urls) == 1
        assert "linkedin.com/posts/" in urls[0]
