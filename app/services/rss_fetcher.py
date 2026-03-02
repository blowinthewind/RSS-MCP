"""RSS feed fetcher service.

This module provides RSS/Atom feed fetching functionality using feedparser.
Handles parsing of various RSS and Atom feed formats.
"""

import logging
from datetime import datetime
from typing import Optional

import feedparser
import httpx

from app.config import settings
from app.models import Source, Article
from app.database import SessionLocal


logger = logging.getLogger(__name__)


class RSSFetcher:
    """
    RSS Feed Fetcher.

    Handles fetching and parsing RSS/Atom feeds from various sources.
    """

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize RSS fetcher.

        Args:
            timeout: Request timeout in seconds. Defaults to settings.request_timeout.
        """
        self.timeout = timeout or settings.request_timeout

    def fetch(self, source: Source) -> list[dict]:
        """
        Fetch and parse RSS feed from a source.

        Args:
            source: Source object with url attribute

        Returns:
            List of parsed feed entries as dictionaries
        """
        try:
            logger.info(f"Fetching feed from {source.name} ({source.url})")

            # Parse the feed
            feed = feedparser.parse(
                source.url,
                timeout=self.timeout,
            )

            # Check for parsing errors
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing warning for {source.name}: {feed.bozo_exception}")

            # Extract entries
            entries = []
            for entry in feed.entries[: settings.max_items_per_source]:
                parsed_entry = self._parse_entry(entry, source)
                if parsed_entry:
                    entries.append(parsed_entry)

            logger.info(f"Fetched {len(entries)} entries from {source.name}")
            return entries

        except Exception as e:
            logger.error(f"Error fetching feed from {source.name}: {e}")
            return []

    def _parse_entry(self, entry: feedparser.FeedParserDict, source: Source) -> Optional[dict]:
        """
        Parse a single feed entry into a dictionary.

        Args:
            entry: Feed entry from feedparser
            source: Source object

        Returns:
            Parsed entry as dictionary, or None if invalid
        """
        try:
            # Get title
            title = entry.get("title", "").strip()
            if not title:
                return None

            # Get URL
            url = ""
            if hasattr(entry, "link"):
                url = entry.link
            elif hasattr(entry, "links") and entry.links:
                for link in entry.links:
                    if link.get("type", "").startswith("text/html"):
                        url = link.get("href", "")
                        break

            if not url:
                return None

            # Get summary/description
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary
            elif hasattr(entry, "description"):
                summary = entry.description

            # Clean summary - remove HTML tags if present
            if summary:
                import re

                summary = re.sub(r"<[^>]+>", "", summary)
                summary = summary.strip()

            # Get author
            author = ""
            if hasattr(entry, "author"):
                author = entry.author
            elif hasattr(entry, "author_detail") and entry.author_detail:
                author = entry.author_detail.get("name", "")

            # Get published date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    published = datetime(*entry.updated_parsed[:6])
                except Exception:
                    pass

            return {
                "title": title,
                "url": url,
                "summary": summary[:2000] if summary else None,
                "author": author or None,
                "published": published,
            }

        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None


def fetch_feed(source: Source) -> list[dict]:
    """
    Convenience function to fetch feed from a source.

    Args:
        source: Source object

    Returns:
        List of parsed feed entries
    """
    fetcher = RSSFetcher()
    return fetcher.fetch(source)


def fetch_all_enabled_sources() -> int:
    """
    Fetch all enabled sources.

    Returns:
        Number of articles fetched
    """
    db = SessionLocal()
    try:
        sources = db.query(Source).filter(Source.enabled == True).all()

        total_articles = 0
        for source in sources:
            articles_data = fetch_feed(source)

            # Check for duplicates and save new articles
            for article_data in articles_data:
                # Check if URL already exists
                existing = db.query(Article).filter(Article.url == article_data["url"]).first()

                if not existing:
                    article = Article(
                        source_id=source.id,
                        **article_data,
                    )
                    db.add(article)
                    total_articles += 1

            # Update last_fetched timestamp
            source.last_fetched = datetime.utcnow()

        db.commit()
        return total_articles

    except Exception as e:
        db.rollback()
        logger.error(f"Error fetching all sources: {e}")
        return 0
    finally:
        db.close()
