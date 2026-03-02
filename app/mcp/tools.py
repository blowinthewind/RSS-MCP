"""MCP Tools implementation.

This module provides MCP tools for RSS feed operations, designed for LLM usage.
"""

import logging
from typing import Optional

from fastmcp import FastMCP

from app.config import settings
from app.database import SessionLocal
from app.models import Source, Article
from app.services.rss_fetcher import fetch_feed
from app.services.content_extract import extract_content
from app.services.scheduler import refresh_source as do_refresh


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
    db = SessionLocal()
    try:
        query = db.query(Source)

        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            for tag in tag_list:
                query = query.filter(Source.tags.contains(tag))

        if enabled is not None:
            query = query.filter(Source.enabled == enabled)

        sources = query.all()

        return {
            "sources": [
                {
                    "id": s.id,
                    "name": s.name,
                    "url": s.url,
                    "tags": s.tags,
                    "enabled": s.enabled,
                    "last_fetched": s.last_fetched.isoformat() if s.last_fetched else None,
                    "article_count": len(s.articles),
                }
                for s in sources
            ],
            "total": len(sources),
        }
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        # Check if URL already exists
        existing = db.query(Source).filter(Source.url == url).first()
        if existing:
            return {
                "success": False,
                "message": f"Source with URL already exists: {existing.name}",
                "source_id": existing.id,
            }

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        # Create source
        source = Source(
            name=name,
            url=url,
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
    finally:
        db.close()


@mcp.tool()
def remove_source(source_id: str) -> dict:
    """
    Remove an RSS source and all its articles.

    Args:
        source_id: ID of the source to remove

    Returns:
        Success message
    """
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {
                "success": False,
                "message": f"Source {source_id} not found",
            }

        source_name = source.name
        db.delete(source)
        db.commit()

        return {
            "success": True,
            "message": f"Source '{source_name}' removed successfully",
        }
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {
                "success": False,
                "message": f"Source {source_id} not found",
            }

        source.enabled = enabled
        db.commit()

        return {
            "success": True,
            "message": f"Source '{source.name}' {'enabled' if enabled else 'disabled'}",
        }
    finally:
        db.close()


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
    db = SessionLocal()
    try:
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
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        # Build query
        q = db.query(Article).join(Source).filter(Source.enabled == True)

        # Filter by source IDs
        if sources:
            source_list = [s.strip() for s in sources.split(",")]
            q = q.filter(Article.source_id.in_(source_list))

        # Filter by tags
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            for tag in tag_list:
                q = q.filter(Source.tags.contains(tag))

        # Apply search filter
        search_term = f"%{query}%"
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
    finally:
        db.close()


@mcp.tool()
def get_article_content(article_id: str) -> dict:
    """
    Get full content of a specific article.

    Args:
        article_id: ID of the article

    Returns:
        Article with full content
    """
    db = SessionLocal()
    try:
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
                    db.commit()
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
    finally:
        db.close()


@mcp.tool()
def refresh_source(source_id: str) -> dict:
    """
    Manually refresh a specific RSS source.

    Args:
        source_id: ID of the source to refresh

    Returns:
        Number of new articles fetched
    """
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {
                "success": False,
                "message": f"Source {source_id} not found",
            }
    finally:
        db.close()

    success = do_refresh(source_id)

    if success:
        # Get count of new articles
        db = SessionLocal()
        try:
            count = db.query(Article).filter(Article.source_id == source_id).count()
            return {
                "success": True,
                "message": f"Source refreshed, {count} total articles",
            }
        finally:
            db.close()
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
