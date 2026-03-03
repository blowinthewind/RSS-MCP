"""Tests for RSS fetcher service."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import feedparser

from app.services.rss_fetcher import RSSFetcher, fetch_feed
from app.models import Source


class MockFeedParserDict:
    """Mock class that behaves like feedparser.FeedParserDict."""
    
    def __init__(self, data):
        self._data = data
        for key, value in data.items():
            setattr(self, key, value)
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __contains__(self, key):
        return key in self._data


class TestRSSFetcher:
    """Test cases for RSSFetcher class."""

    @pytest.fixture
    def fetcher(self):
        """Create RSSFetcher instance for testing."""
        return RSSFetcher(timeout=30, max_retries=3)

    @pytest.fixture
    def mock_source(self):
        """Create mock source for testing."""
        source = Mock(spec=Source)
        source.name = "Test Source"
        source.url = "https://example.com/feed.xml"
        return source

    def test_init_default_values(self):
        """Test RSSFetcher initializes with default values."""
        fetcher = RSSFetcher()
        assert fetcher.timeout == 30  # From settings
        assert fetcher.max_retries == 3

    def test_init_custom_values(self):
        """Test RSSFetcher initializes with custom values."""
        fetcher = RSSFetcher(timeout=60, max_retries=5)
        assert fetcher.timeout == 60
        assert fetcher.max_retries == 5

    @patch('app.services.rss_fetcher.feedparser.parse')
    def test_fetch_success(self, mock_parse, fetcher, mock_source):
        """Test successful feed fetching."""
        # Mock feedparser response using FeedParserDict-like object
        mock_entry = MockFeedParserDict({
            'title': 'Test Article',
            'link': 'https://example.com/article',
            'summary': 'Test summary',
            'author': 'Test Author',
            'published_parsed': (2024, 1, 1, 0, 0, 0, 0, 0, 0),
        })

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = False
        mock_feed.bozo_exception = None

        mock_parse.return_value = mock_feed

        result = fetcher.fetch(mock_source)

        assert len(result) == 1
        assert result[0]['title'] == "Test Article"
        assert result[0]['url'] == "https://example.com/article"
        assert result[0]['author'] == "Test Author"
        mock_parse.assert_called_once_with("https://example.com/feed.xml")

    @patch('app.services.rss_fetcher.feedparser.parse')
    def test_fetch_empty_feed(self, mock_parse, fetcher, mock_source):
        """Test fetching empty feed."""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feed.bozo = False
        mock_feed.bozo_exception = None

        mock_parse.return_value = mock_feed

        result = fetcher.fetch(mock_source)

        assert result == []

    @patch('app.services.rss_fetcher.feedparser.parse')
    def test_fetch_with_bozo_exception(self, mock_parse, fetcher, mock_source):
        """Test fetching feed with bozo exception (parsing warning)."""
        mock_entry = MockFeedParserDict({
            'title': 'Test Article',
            'link': 'https://example.com/article',
            'summary': 'Test summary',
            'author': None,
            'published_parsed': None,
            'updated_parsed': None,
        })

        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feed.bozo = True
        mock_feed.bozo_exception = Exception("Character encoding issue")

        mock_parse.return_value = mock_feed

        result = fetcher.fetch(mock_source)

        assert len(result) == 1
        assert result[0]['title'] == "Test Article"

    @patch('app.services.rss_fetcher.feedparser.parse')
    def test_fetch_exception(self, mock_parse, fetcher, mock_source):
        """Test fetch handling exception."""
        mock_parse.side_effect = Exception("Network error")

        result = fetcher.fetch(mock_source)

        assert result == []

    def test_parse_entry_valid(self, fetcher, mock_source):
        """Test parsing valid entry."""
        entry = MockFeedParserDict({
            'title': '  Test Title  ',
            'link': 'https://example.com/article',
            'summary': '<p>Test summary</p>',
            'author': 'Test Author',
            'published_parsed': (2024, 1, 1, 0, 0, 0, 0, 0, 0),
        })

        result = fetcher._parse_entry(entry, mock_source)

        assert result is not None
        assert result['title'] == "Test Title"
        assert result['url'] == "https://example.com/article"
        assert result['summary'] == "Test summary"
        assert result['author'] == "Test Author"
        assert isinstance(result['published'], datetime)

    def test_parse_entry_no_title(self, fetcher, mock_source):
        """Test parsing entry without title."""
        entry = MockFeedParserDict({
            'title': '   ',
            'link': 'https://example.com/article',
        })

        result = fetcher._parse_entry(entry, mock_source)

        assert result is None

    def test_parse_entry_no_url(self, fetcher, mock_source):
        """Test parsing entry without URL."""
        entry = MockFeedParserDict({
            'title': 'Test Title',
            'link': '',
            'links': [],
        })

        result = fetcher._parse_entry(entry, mock_source)

        assert result is None

    def test_parse_entry_with_links_attribute(self, fetcher, mock_source):
        """Test parsing entry with links attribute."""
        # Create a mock entry that simulates feedparser.FeedParserDict behavior
        # Note: link must not exist as attribute for fallback to links to work
        class MockEntryWithLinks:
            def __init__(self):
                self.title = 'Test Title'
                # Don't set link attribute - let it fall back to links
                self.links = [
                    {'type': 'text/html', 'href': 'https://example.com/article'}
                ]
                self.summary = 'Test summary'
                self.author = None
                self.published_parsed = None
                self.updated_parsed = None

            def get(self, key, default=None):
                return getattr(self, key, default)

            def __hasattr__(self, name):
                return name in self.__dict__

        entry = MockEntryWithLinks()

        result = fetcher._parse_entry(entry, mock_source)

        assert result is not None
        assert result['url'] == "https://example.com/article"

    def test_parse_entry_html_in_summary(self, fetcher, mock_source):
        """Test that HTML tags are removed from summary."""
        entry = MockFeedParserDict({
            'title': 'Test Title',
            'link': 'https://example.com/article',
            'summary': '<div><p>Test <b>summary</b></p></div>',
            'author': None,
            'published_parsed': None,
            'updated_parsed': None,
        })

        result = fetcher._parse_entry(entry, mock_source)

        assert result is not None
        assert "<" not in result['summary']
        assert ">" not in result['summary']

    def test_parse_entry_updated_parsed_fallback(self, fetcher, mock_source):
        """Test using updated_parsed when published_parsed is missing."""
        entry = MockFeedParserDict({
            'title': 'Test Title',
            'link': 'https://example.com/article',
            'summary': 'Test summary',
            'author': None,
            'published_parsed': None,
            'updated_parsed': (2024, 6, 15, 12, 0, 0, 0, 0, 0),
        })

        result = fetcher._parse_entry(entry, mock_source)

        assert result is not None
        assert isinstance(result['published'], datetime)

    def test_parse_entry_author_from_author_detail(self, fetcher, mock_source):
        """Test extracting author from author_detail."""
        # Create a mock entry that simulates feedparser.FeedParserDict behavior
        # Note: author must not exist as attribute for fallback to author_detail to work
        class MockEntryWithAuthorDetail:
            def __init__(self):
                self.title = 'Test Title'
                self.link = 'https://example.com/article'
                self.summary = 'Test summary'
                # Don't set author attribute - let it fall back to author_detail
                self.author_detail = {'name': 'Detail Author'}
                self.published_parsed = None
                self.updated_parsed = None

            def get(self, key, default=None):
                return getattr(self, key, default)

            def __hasattr__(self, name):
                return name in self.__dict__

        entry = MockEntryWithAuthorDetail()

        result = fetcher._parse_entry(entry, mock_source)

        assert result is not None
        assert result['author'] == "Detail Author"

    def test_parse_entry_summary_truncation(self, fetcher, mock_source):
        """Test that long summaries are truncated."""
        entry = MockFeedParserDict({
            'title': 'Test Title',
            'link': 'https://example.com/article',
            'summary': 'A' * 3000,  # Very long summary
            'author': None,
            'published_parsed': None,
            'updated_parsed': None,
        })

        result = fetcher._parse_entry(entry, mock_source)

        assert result is not None
        assert len(result['summary']) <= 2000

    def test_parse_entry_exception_handling(self, fetcher, mock_source):
        """Test exception handling in parse_entry."""
        entry = Mock()
        entry.title = "Test Title"
        # Make entry.link raise an exception
        del entry.link
        entry.links = None  # This will cause AttributeError

        result = fetcher._parse_entry(entry, mock_source)

        assert result is None


class TestFetchFeed:
    """Test cases for fetch_feed function."""

    @patch('app.services.rss_fetcher.RSSFetcher')
    def test_fetch_feed(self, mock_fetcher_class):
        """Test fetch_feed convenience function."""
        mock_fetcher = Mock()
        mock_fetcher.fetch.return_value = [{'title': 'Test'}]
        mock_fetcher_class.return_value = mock_fetcher

        mock_source = Mock(spec=Source)
        result = fetch_feed(mock_source)

        assert result == [{'title': 'Test'}]
        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch.assert_called_once_with(mock_source)


class TestFetchAllEnabledSources:
    """Test cases for fetch_all_enabled_sources function."""

    @patch('app.services.rss_fetcher.get_db_session')
    @patch('app.services.rss_fetcher.fetch_feed')
    def test_fetch_all_enabled_sources_success(
        self, mock_fetch_feed, mock_get_db_session
    ):
        """Test successful fetching from all enabled sources."""
        # Mock database session
        mock_db = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_db)
        mock_context.__exit__ = Mock(return_value=False)
        mock_get_db_session.return_value = mock_context

        # Mock sources
        mock_source1 = Mock(spec=Source)
        mock_source1.id = "source1"
        mock_source1.enabled = True
        mock_source1.last_fetched = None

        mock_source2 = Mock(spec=Source)
        mock_source2.id = "source2"
        mock_source2.enabled = True
        mock_source2.last_fetched = None

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_source1,
            mock_source2,
        ]

        # Mock article query (no duplicates)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock fetch_feed return
        mock_fetch_feed.side_effect = [
            [
                {
                    'title': 'Article 1',
                    'url': 'https://example.com/1',
                    'summary': 'Summary 1',
                    'author': 'Author 1',
                    'published': datetime.now(),
                }
            ],
            [
                {
                    'title': 'Article 2',
                    'url': 'https://example.com/2',
                    'summary': 'Summary 2',
                    'author': 'Author 2',
                    'published': datetime.now(),
                }
            ],
        ]

        from app.services.rss_fetcher import fetch_all_enabled_sources

        result = fetch_all_enabled_sources()

        assert result == 2  # 2 new articles
        assert mock_source1.last_fetched is not None
        assert mock_source2.last_fetched is not None

    @patch('app.services.rss_fetcher.get_db_session')
    @patch('app.services.rss_fetcher.fetch_feed')
    def test_fetch_all_skips_duplicates(
        self, mock_fetch_feed, mock_get_db_session
    ):
        """Test that duplicate articles are skipped."""
        # Mock database session
        mock_db = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_db)
        mock_context.__exit__ = Mock(return_value=False)
        mock_get_db_session.return_value = mock_context

        # Mock source
        mock_source = Mock(spec=Source)
        mock_source.id = "source1"
        mock_source.enabled = True
        mock_source.last_fetched = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_source]

        # First call returns existing article, second returns new
        existing_article = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            existing_article,  # First article exists (duplicate)
            None,  # Second article is new
        ]

        mock_fetch_feed.return_value = [
            {'title': 'Article 1', 'url': 'https://example.com/1'},
            {'title': 'Article 2', 'url': 'https://example.com/2'},
        ]

        from app.services.rss_fetcher import fetch_all_enabled_sources

        result = fetch_all_enabled_sources()

        assert result == 1  # Only 1 new article

    @patch('app.services.rss_fetcher.get_db_session')
    def test_fetch_all_handles_exception(self, mock_get_db_session):
        """Test exception handling in fetch_all_enabled_sources."""
        # Mock database session to raise exception
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_db)
        mock_context.__exit__ = Mock(return_value=False)
        mock_get_db_session.return_value = mock_context

        from app.services.rss_fetcher import fetch_all_enabled_sources

        result = fetch_all_enabled_sources()

        assert result == 0
