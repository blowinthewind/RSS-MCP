"""Tests for content extraction service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from app.services.content_extract import ContentExtractor, extract_content


class TestContentExtractor:
    """Test cases for ContentExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create ContentExtractor instance for testing."""
        return ContentExtractor(timeout=30)

    def test_init_default_values(self):
        """Test ContentExtractor initializes with default values."""
        extractor = ContentExtractor()
        assert extractor.timeout == 30  # From settings

    def test_init_custom_values(self):
        """Test ContentExtractor initializes with custom values."""
        extractor = ContentExtractor(timeout=60)
        assert extractor.timeout == 60

    @patch('app.services.content_extract.settings')
    @patch('app.services.content_extract.httpx.Client')
    @patch('app.services.content_extract.trafilatura.extract')
    def test_extract_success(self, mock_trafilatura_extract, mock_client_class, mock_settings, extractor):
        """Test successful content extraction."""
        mock_settings.enable_content_extraction = True

        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Mock trafilatura extraction
        mock_trafilatura_extract.return_value = "Extracted test content"

        result = extractor.extract("https://example.com/article")

        assert result == "Extracted test content"
        mock_client.get.assert_called_once_with("https://example.com/article")
        mock_trafilatura_extract.assert_called_once()

    @patch('app.services.content_extract.settings')
    def test_extract_disabled(self, mock_settings, extractor):
        """Test extraction when disabled in settings."""
        mock_settings.enable_content_extraction = False

        result = extractor.extract("https://example.com/article")

        assert result is None

    @patch('app.services.content_extract.settings')
    @patch('app.services.content_extract.httpx.Client')
    def test_extract_timeout(self, mock_client_class, mock_settings, extractor):
        """Test handling of timeout exception."""
        mock_settings.enable_content_extraction = True

        # Mock HTTP client to raise timeout
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
        mock_client_class.return_value = mock_client

        result = extractor.extract("https://example.com/article")

        assert result is None

    @patch('app.services.content_extract.settings')
    @patch('app.services.content_extract.httpx.Client')
    def test_extract_http_error(self, mock_client_class, mock_settings, extractor):
        """Test handling of HTTP error."""
        mock_settings.enable_content_extraction = True

        # Mock HTTP client to raise HTTP error
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.side_effect = httpx.HTTPError("404 Not Found")
        mock_client_class.return_value = mock_client

        result = extractor.extract("https://example.com/article")

        assert result is None

    @patch('app.services.content_extract.settings')
    @patch('app.services.content_extract.httpx.Client')
    @patch('app.services.content_extract.trafilatura.extract')
    def test_extract_no_content(self, mock_trafilatura_extract, mock_client_class, mock_settings, extractor):
        """Test extraction when no content is found."""
        mock_settings.enable_content_extraction = True

        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Mock trafilatura returning None (no content extracted)
        mock_trafilatura_extract.return_value = None

        result = extractor.extract("https://example.com/article")

        assert result is None

    @patch('app.services.content_extract.settings')
    @patch('app.services.content_extract.httpx.Client')
    @patch('app.services.content_extract.trafilatura.extract')
    def test_extract_trafilatura_options(self, mock_trafilatura_extract, mock_client_class, mock_settings, extractor):
        """Test that trafilatura is called with correct options."""
        mock_settings.enable_content_extraction = True

        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        mock_trafilatura_extract.return_value = "Content"

        extractor.extract("https://example.com/article")

        # Verify trafilatura was called with correct options
        mock_trafilatura_extract.assert_called_once_with(
            "<html><body>Content</body></html>",
            include_comments=False,
            include_tables=True,
            output_format="text",
        )

    @patch('app.services.content_extract.settings')
    @patch('app.services.content_extract.httpx.Client')
    def test_extract_generic_exception(self, mock_client_class, mock_settings, extractor):
        """Test handling of generic exception."""
        mock_settings.enable_content_extraction = True

        # Mock HTTP client to raise generic exception
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.side_effect = Exception("Unexpected error")
        mock_client_class.return_value = mock_client

        result = extractor.extract("https://example.com/article")

        assert result is None


class TestExtractContent:
    """Test cases for extract_content convenience function."""

    @patch('app.services.content_extract.ContentExtractor')
    def test_extract_content(self, mock_extractor_class):
        """Test extract_content convenience function."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = "Extracted content"
        mock_extractor_class.return_value = mock_extractor

        result = extract_content("https://example.com/article")

        assert result == "Extracted content"
        mock_extractor_class.assert_called_once()
        mock_extractor.extract.assert_called_once_with("https://example.com/article")

    @patch('app.services.content_extract.ContentExtractor')
    def test_extract_content_failure(self, mock_extractor_class):
        """Test extract_content when extraction fails."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = None
        mock_extractor_class.return_value = mock_extractor

        result = extract_content("https://example.com/article")

        assert result is None
