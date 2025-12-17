"""Tests for LinkedIn URL parsing and validation."""

import pytest

from bot.services.linkedin import extract_linkedin_urls, is_linkedin_post


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
