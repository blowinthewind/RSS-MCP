"""MCP Resources implementation.

This module provides MCP resources for accessing RSS data.
"""

import json
import logging
from typing import Optional

from app.config import settings
from app.database import SessionLocal
from app.models import Source, Article


logger = logging.getLogger(__name__)


def get_sources_list() -> str:
    """
    Get list of all RSS sources as JSON.

    Returns:
        JSON string of all sources
    """
    db = SessionLocal()
    try:
        sources = db.query(Source).all()

        result = {
            "sources": [
                {
                    "id": s.id,
                    "name": s.name,
                    "url": s.url,
                    "tags": s.tags,
                    "enabled": s.enabled,
                    "article_count": len(s.articles),
                    "last_fetched": s.last_fetched.isoformat() if s.last_fetched else None,
                }
                for s in sources
            ],
            "total": len(sources),
        }

        return json.dumps(result, indent=2)
    finally:
        db.close()


def get_sources_by_tag(tag: str) -> str:
    """
    Get sources filtered by tag as JSON.

    Args:
        tag: Tag to filter by

    Returns:
        JSON string of filtered sources
    """
    db = SessionLocal()
    try:
        sources = db.query(Source).filter(Source.tags.contains([tag])).all()

        result = {
            "tag": tag,
            "sources": [
                {
                    "id": s.id,
                    "name": s.name,
                    "url": s.url,
                    "tags": s.tags,
                    "enabled": s.enabled,
                    "article_count": len(s.articles),
                }
                for s in sources
            ],
            "total": len(sources),
        }

        return json.dumps(result, indent=2)
    finally:
        db.close()


def get_feed_latest(source_id: str, limit: int = 10) -> str:
    """
    Get latest articles from a source as JSON.

    Args:
        source_id: Source ID
        limit: Maximum articles to return

    Returns:
        JSON string of articles
    """
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return json.dumps({"error": f"Source {source_id} not found"})

        articles = (
            db.query(Article)
            .filter(Article.source_id == source_id)
            .order_by(Article.published.desc().nullslast())
            .limit(limit)
            .all()
        )

        result = {
            "source": {
                "id": source.id,
                "name": source.name,
            },
            "items": [
                {
                    "id": a.id,
                    "title": a.title,
                    "url": a.url,
                    "summary": a.summary,
                    "published": a.published.isoformat() if a.published else None,
                }
                for a in articles
            ],
            "total": len(articles),
        }

        return json.dumps(result, indent=2)
    finally:
        db.close()


def get_config() -> str:
    """
    Get current configuration as JSON.

    Returns:
        JSON string of configuration
    """
    db = SessionLocal()
    try:
        total_sources = db.query(Source).count()
        total_articles = db.query(Article).count()

        result = {
            "mcp_name": settings.mcp_name,
            "mcp_version": settings.mcp_version,
            "deployment": settings.deployment,
            "auth_enabled": settings.auth_enabled,
            "database_url": settings.database_url.split("@")[-1]
            if "@" in settings.database_url
            else settings.database_url,  # Hide credentials
            "default_fetch_interval": settings.default_fetch_interval,
            "enable_content_extraction": settings.enable_content_extraction,
            "stats": {
                "total_sources": total_sources,
                "total_articles": total_articles,
                "enabled_sources": db.query(Source).filter(Source.enabled == True).count(),
            },
        }

        return json.dumps(result, indent=2)
    finally:
        db.close()
