"""MCP Tools implementation.

This module provides MCP tools for RSS feed operations, designed for LLM usage.
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

from fastmcp import FastMCP

from app.config import settings
from app.database import get_db_session
from app.models import Source, Article
from app.services.rss_fetcher import fetch_feed
from app.services.content_extract import extract_content
from app.services.scheduler import refresh_source as do_refresh
from app.utils import split_by_comma


logger = logging.getLogger(__name__)

# Create MCP instance
mcp = FastMCP(settings.mcp_name)


@mcp.tool()
def list_sources(
    tags: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> dict:
    """
    List all RSS sources with optional filtering.

    Use this tool to get an overview of available RSS sources.
    This should be called first to understand what sources are available.

    Args:
        tags: Comma-separated tags to filter (e.g., "tech,ai")
        enabled: Filter by enabled status (true/false)

    Returns:
        List of sources with their IDs, names, and tags
    """
    with get_db_session() as db:
        query = db.query(Source)

        if tags:
            tag_list = split_by_comma(tags)
            for tag in tag_list:
                query = query.filter(Source.tags.contains(tag))

        if enabled is not None:
            query = query.filter(Source.enabled == enabled)

        sources = query.all()

        # Get article counts in a single query to avoid N+1
        from sqlalchemy import func
        article_counts = dict(
            db.query(Article.source_id, func.count(Article.id))
            .group_by(Article.source_id)
            .all()
        )

        return {
            "sources": [
                {
                    "id": s.id,
                    "name": s.name,
                    "url": s.url,
                    "tags": s.tags,
                    "enabled": s.enabled,
                    "last_fetched": s.last_fetched.isoformat() if s.last_fetched else None,
                    "article_count": article_counts.get(s.id, 0),
                }
                for s in sources
            ],
            "total": len(sources),
        }


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    url = url.strip()

    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format: must include scheme (http/https) and domain"

        if result.scheme not in ["http", "https"]:
            return False, f"Invalid URL scheme: {result.scheme}. Only http and https are allowed"

        # Basic domain validation
        domain = result.netloc.lower()
        if not domain or "." not in domain:
            return False, "Invalid domain in URL"

        return True, ""
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


@mcp.tool()
def add_source(
    url: str,
    name: str,
    tags: str = "",
    fetch_interval: int = 300,
) -> dict:
    """
    Add a new RSS source.

    Args:
        url: RSS feed URL
        name: Display name for the source
        tags: Comma-separated tags (e.g., "tech,ai,news")
        fetch_interval: Fetch interval in seconds (default: 300)

    Returns:
        Created source information
    """
    # Validate URL format
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        return {
            "success": False,
            "message": error_msg,
        }

    # Validate name
    if not name or not name.strip():
        return {
            "success": False,
            "message": "Source name cannot be empty",
        }

    # Validate fetch_interval
    if fetch_interval < 60:
        return {
            "success": False,
            "message": "Fetch interval must be at least 60 seconds",
        }

    with get_db_session() as db:
        # Check if URL already exists
        existing = db.query(Source).filter(Source.url == url).first()
        if existing:
            return {
                "success": False,
                "message": f"Source with URL already exists: {existing.name}",
                "source_id": existing.id,
            }

        # Parse tags (handles both English and Chinese commas)
        tag_list = split_by_comma(tags)

        # Create source
        source = Source(
            name=name.strip(),
            url=url.strip(),
            tags=tag_list,
            fetch_interval=fetch_interval,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        # Try to fetch initial articles
        try:
            articles_data = fetch_feed(source)
            for article_data in articles_data:
                article = Article(
                    source_id=source.id,
                    title=article_data["title"],
                    url=article_data["url"],
                    summary=article_data.get("summary"),
                    author=article_data.get("author"),
                    published=article_data.get("published"),
                )
                db.add(article)
            db.commit()
        except Exception as e:
            logger.warning(f"Initial fetch failed: {e}")
            db.rollback()

        return {
            "success": True,
            "message": f"Source '{name}' added successfully",
            "source_id": source.id,
            "tags": source.tags,
        }


@mcp.tool()
def remove_source(source_id: str) -> dict:
    """
    Remove an RSS source.

    Args:
        source_id: ID of the source to remove

    Returns:
        Success message
    """
    with get_db_session() as db:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {
                "success": False,
                "message": f"Source {source_id} not found",
            }

        source_name = source.name
        db.delete(source)

        return {
            "success": True,
            "message": f"Source '{source_name}' removed successfully",
        }


@mcp.tool()
def enable_source(source_id: str, enabled: bool = True) -> dict:
    """
    Enable or disable an RSS source.

    Args:
        source_id: ID of the source
        enabled: True to enable, False to disable

    Returns:
        Success message
    """
    with get_db_session() as db:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {
                "success": False,
                "message": f"Source {source_id} not found",
            }

        source.enabled = enabled

        return {
            "success": True,
            "message": f"Source '{source.name}' {'enabled' if enabled else 'disabled'}",
        }


@mcp.tool()
def get_feed_items(
    source_id: str,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """
    Get articles from a specific RSS source.

    Args:
        source_id: ID of the source
        limit: Maximum number of articles to return (default: 10)
        offset: Offset for pagination (default: 0)

    Returns:
        List of articles with title, summary, URL, and published date
    """
    with get_db_session() as db:
        # Check if source exists
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {
                "success": False,
                "message": f"Source {source_id} not found",
            }

        # Get articles
        articles = (
            db.query(Article)
            .filter(Article.source_id == source_id)
            .order_by(Article.published.desc().nullslast())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
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
                    "author": a.author,
                    "published": a.published.isoformat() if a.published else None,
                    "fetched_at": a.fetched_at.isoformat(),
                }
                for a in articles
            ],
            "total": db.query(Article).filter(Article.source_id == source_id).count(),
            "offset": offset,
            "limit": limit,
        }


def escape_like_pattern(pattern: str) -> str:
    """
    Escape special characters in LIKE pattern.

    SQL LIKE special characters:
    - % matches any sequence of characters
    - _ matches any single character
    - \ is the escape character

    Args:
        pattern: Raw search pattern

    Returns:
        Escaped pattern safe for LIKE queries
    """
    # Escape backslash first, then % and _
    return pattern.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@mcp.tool()
def search_feeds(
    query: str,
    sources: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 10,
) -> dict:
    """
    Search articles across RSS sources.

    This is the main tool for finding specific content.
    Use this when users ask about specific topics.

    Args:
        query: Search query (e.g., "AI", "machine learning", "startup")
        sources: Comma-separated source IDs to search (optional)
        tags: Comma-separated tags to filter (optional)
        limit: Maximum number of results (default: 10)

    Returns:
        List of matching articles with content
    """
    # Validate and sanitize query
    if not query or not query.strip():
        return {
            "query": "",
            "items": [],
            "total": 0,
            "returned": 0,
            "message": "Search query cannot be empty",
        }

    # Limit query length to prevent abuse
    max_query_length = 200
    if len(query) > max_query_length:
        query = query[:max_query_length]

    with get_db_session() as db:
        # Build query
        q = db.query(Article).join(Source).filter(Source.enabled == True)

        # Filter by source IDs
        if sources:
            source_list = split_by_comma(sources)
            if source_list:
                q = q.filter(Article.source_id.in_(source_list))

        # Filter by tags
        if tags:
            tag_list = split_by_comma(tags)
            for tag in tag_list:
                q = q.filter(Source.tags.contains(tag))

        # Apply search filter with escaped special characters
        escaped_query = escape_like_pattern(query.strip())
        search_term = f"%{escaped_query}%"
        q = q.filter(
            Article.title.ilike(search_term)
            | Article.summary.ilike(search_term)
            | Article.content.ilike(search_term)
        )

        # Get total count
        total = q.count()

        # Get articles
        articles = q.order_by(Article.published.desc().nullslast()).limit(limit).all()

        # Get source info for each article
        source_ids = set(a.source_id for a in articles)
        sources_info = {
            s.id: s.name for s in db.query(Source).filter(Source.id.in_(source_ids)).all()
        }

        return {
            "query": query,
            "items": [
                {
                    "id": a.id,
                    "source_id": a.source_id,
                    "source_name": sources_info.get(a.source_id, "Unknown"),
                    "title": a.title,
                    "url": a.url,
                    "summary": a.summary,
                    "author": a.author,
                    "published": a.published.isoformat() if a.published else None,
                }
                for a in articles
            ],
            "total": total,
            "returned": len(articles),
        }


@mcp.tool()
def get_article_content(article_id: str) -> dict:
    """
    Get full content of a specific article.

    Args:
        article_id: ID of the article

    Returns:
        Article with full content
    """
    with get_db_session() as db:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return {
                "success": False,
                "message": f"Article {article_id} not found",
            }

        # If content not stored, try to extract
        if not article.content:
            try:
                content = extract_content(article.url)
                if content:
                    article.content = content
            except Exception as e:
                logger.warning(f"Failed to extract content: {e}")

        # Get source name
        source = db.query(Source).filter(Source.id == article.source_id).first()

        return {
            "success": True,
            "article": {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "summary": article.summary,
                "content": article.content,
                "author": article.author,
                "source_name": source.name if source else "Unknown",
                "published": article.published.isoformat() if article.published else None,
            },
        }


@mcp.tool()
def refresh_source(source_id: str) -> dict:
    """
    Manually refresh a specific RSS source.

    Args:
        source_id: ID of the source to refresh

    Returns:
        Number of new articles fetched
    """
    with get_db_session() as db:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {
                "success": False,
                "message": f"Source {source_id} not found",
            }

    success = do_refresh(source_id)

    if success:
        # Get count of new articles
        with get_db_session() as db:
            count = db.query(Article).filter(Article.source_id == source_id).count()
            return {
                "success": True,
                "message": f"Source refreshed, {count} total articles",
            }
    else:
        return {
            "success": False,
            "message": "Failed to refresh source",
        }


@mcp.tool()
def refresh_all() -> dict:
    """
    Refresh all enabled RSS sources.

    Returns:
        Summary of refresh operation
    """
    from app.services.rss_fetcher import fetch_all_enabled_sources

    count = fetch_all_enabled_sources()

    return {
        "success": True,
        "message": f"Refreshed all sources, {count} new articles fetched",
    }
