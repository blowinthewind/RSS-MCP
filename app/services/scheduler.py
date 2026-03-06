"""Scheduler service for periodic RSS fetching.

This module provides background scheduling for automatic RSS feed fetching
using APScheduler.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import get_db_session
from app.models import Source
from app.services.rss_fetcher import fetch_feed
from app.services.content_extract import extract_content
from app.config import settings


logger = logging.getLogger(__name__)

# Thread pool for running content extraction without blocking
_content_extract_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="content-extract-")

# Thread pool for concurrent source fetching
_source_fetch_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="source-fetch-")


class Scheduler:
    """
    Background Scheduler for RSS fetching.

    Manages periodic fetching of RSS feeds from enabled sources.
    """

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = BackgroundScheduler()

    def start(self, run_immediately: bool = True):
        """Start the scheduler.

        Args:
            run_immediately: If True, run fetch immediately on start.
        """
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return

        # Add job to fetch all sources
        self.scheduler.add_job(
            func=self.fetch_all_sources,
            trigger=IntervalTrigger(seconds=settings.default_fetch_interval),
            id="fetch_all_sources",
            name="Fetch all RSS sources",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Scheduler started")

        # Run immediately if requested
        if run_immediately:
            logger.info("Running initial fetch immediately...")
            self.fetch_all_sources()

    def stop(self, wait: bool = False, timeout: Optional[int] = 10):
        """Stop the scheduler.

        Args:
            wait: If True, wait for jobs to complete. If False, shutdown immediately.
            timeout: Seconds to wait for jobs to complete (None = wait forever).
        """
        if not self.scheduler.running:
            return

        try:
            self.scheduler.shutdown(wait=wait, timeout=timeout)
            logger.info(f"Scheduler stopped (wait={wait}, timeout={timeout})")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    def fetch_all_sources(self):
        """
        Fetch all enabled sources and extract content.

        This is the main job that runs periodically.
        Uses concurrent fetching for better performance.
        """
        logger.info("Starting scheduled fetch of all sources")

        with get_db_session() as db:
            sources = db.query(Source).filter(Source.enabled == True).all()

        if not sources:
            logger.info("No enabled sources to fetch")
            return

        # Fetch sources concurrently using thread pool
        futures = []
        for source in sources:
            future = _source_fetch_executor.submit(self._fetch_source_concurrent, source)
            futures.append((source, future))

        # Wait for all fetches to complete
        for source, future in futures:
            try:
                future.result(timeout=60)  # 60 second timeout per source
            except Exception as e:
                logger.error(f"Error fetching source {source.name}: {e}")

        logger.info(f"Scheduled fetch completed for {len(sources)} sources")

    def _fetch_source_concurrent(self, source: Source):
        """
        Fetch a single source with its own database session.

        Args:
            source: Source object to fetch
        """
        with get_db_session() as db:
            # Refresh source object in new session
            source = db.query(Source).filter(Source.id == source.id).first()
            if source:
                self._fetch_source(db, source)

    def _fetch_source(self, db, source: Source):
        """
        Fetch a single source and save articles.

        Args:
            db: Database session
            source: Source object to fetch
        """
        from app.models import Article

        logger.info(f"Fetching source: {source.name}")

        # Fetch feed entries
        articles_data = fetch_feed(source)

        for article_data in articles_data:
            # Check if URL already exists (deduplication)
            existing = db.query(Article).filter(Article.url == article_data["url"]).first()

            if not existing:
                # Create new article
                article = Article(
                    source_id=source.id,
                    title=article_data["title"],
                    url=article_data["url"],
                    summary=article_data.get("summary"),
                    author=article_data.get("author"),
                    published=article_data.get("published"),
                )
                db.add(article)

                # Extract content if enabled (run in thread pool to avoid blocking)
                if settings.enable_content_extraction:
                    try:
                        content = _content_extract_executor.submit(
                            extract_content, article.url
                        ).result(timeout=30)
                        if content:
                            article.content = content
                    except Exception as e:
                        logger.warning(f"Failed to extract content: {e}")

        # Update last_fetched timestamp
        source.last_fetched = datetime.now(timezone.utc)

    def refresh_source(self, source_id: str):
        """
        Manually refresh a specific source.

        Args:
            source_id: ID of the source to refresh
        """
        try:
            with get_db_session() as db:
                source = db.query(Source).filter(Source.id == source_id).first()
                if not source:
                    logger.warning(f"Source {source_id} not found")
                    return False

                self._fetch_source(db, source)
                return True

        except Exception as e:
            logger.error(f"Error refreshing source {source_id}: {e}")
            return False


# Global scheduler instance
scheduler = Scheduler()


def start_scheduler():
    """Start the global scheduler."""
    scheduler.start()


def stop_scheduler(wait: bool = False, timeout: Optional[int] = 10):
    """Stop the global scheduler.

    Args:
        wait: If True, wait for jobs to complete. If False, shutdown immediately.
        timeout: Seconds to wait for jobs to complete.
    """
    scheduler.stop(wait=wait, timeout=timeout)


def refresh_source(source_id: str) -> bool:
    """
    Manually refresh a specific source.

    Args:
        source_id: ID of the source to refresh

    Returns:
        True if successful, False otherwise
    """
    return scheduler.refresh_source(source_id)
