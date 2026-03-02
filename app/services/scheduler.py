"""Scheduler service for periodic RSS fetching.

This module provides background scheduling for automatic RSS feed fetching
using APScheduler.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.models import Source
from app.services.rss_fetcher import fetch_feed
from app.services.content_extract import extract_content
from app.config import settings


logger = logging.getLogger(__name__)


class Scheduler:
    """
    Background Scheduler for RSS fetching.

    Manages periodic fetching of RSS feeds from enabled sources.
    """

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = BackgroundScheduler()

    def start(self):
        """Start the scheduler."""
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

    def stop(self):
        """Stop the scheduler."""
        if not self.scheduler.running:
            return

        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def fetch_all_sources(self):
        """
        Fetch all enabled sources and extract content.

        This is the main job that runs periodically.
        """
        logger.info("Starting scheduled fetch of all sources")

        db = SessionLocal()
        try:
            sources = db.query(Source).filter(Source.enabled == True).all()

            for source in sources:
                try:
                    self._fetch_source(db, source)
                except Exception as e:
                    logger.error(f"Error fetching source {source.name}: {e}")

            db.commit()
            logger.info("Scheduled fetch completed")

        except Exception as e:
            db.rollback()
            logger.error(f"Error in scheduled fetch: {e}")
        finally:
            db.close()

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

                # Extract content if enabled
                if settings.enable_content_extraction:
                    try:
                        content = extract_content(article.url)
                        if content:
                            article.content = content
                    except Exception as e:
                        logger.warning(f"Failed to extract content: {e}")

        # Update last_fetched timestamp
        source.last_fetched = datetime.utcnow()

    def refresh_source(self, source_id: str):
        """
        Manually refresh a specific source.

        Args:
            source_id: ID of the source to refresh
        """
        db = SessionLocal()
        try:
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                logger.warning(f"Source {source_id} not found")
                return False

            self._fetch_source(db, source)
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error refreshing source {source_id}: {e}")
            return False
        finally:
            db.close()


# Global scheduler instance
scheduler = Scheduler()


def start_scheduler():
    """Start the global scheduler."""
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    scheduler.stop()


def refresh_source(source_id: str) -> bool:
    """
    Manually refresh a specific source.

    Args:
        source_id: ID of the source to refresh

    Returns:
        True if successful, False otherwise
    """
    return scheduler.refresh_source(source_id)
