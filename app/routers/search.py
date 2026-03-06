"""Search API routes.

This module provides API endpoints for searching RSS articles.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source, Article
from app.schemas import ArticleResponse, ArticleListResponse, SearchResponse
from app.utils import split_by_comma


logger = logging.getLogger(__name__)


def escape_like_pattern(pattern: str) -> str:
    """
    Escape special characters in LIKE pattern.

    SQL LIKE special characters:
    - % matches any sequence of characters
    - _ matches any single character
    - \\ is the escape character

    Args:
        pattern: Raw search pattern

    Returns:
        Escaped pattern safe for LIKE queries
    """
    # Escape backslash first, then % and _
    return pattern.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

# Create router
router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=ArticleListResponse)
def search_articles(
    q: str = Query(..., description="Search query"),
    sources: Optional[str] = Query(None, description="Comma-separated source IDs"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(10, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """
    Search articles by query string.

    Supports filtering by source IDs and tags.
    Search is performed on title and summary fields (content excluded for performance).
    """
    # Start with base query
    query = db.query(Article).join(Source)

    # Filter by enabled sources first (reduces search scope)
    query = query.filter(Source.enabled == True)

    # Filter by source IDs if provided (further reduces scope)
    if sources:
        source_id_list = split_by_comma(sources)
        query = query.filter(Article.source_id.in_(source_id_list))

    # Filter by tags if provided
    if tags:
        tag_list = split_by_comma(tags)
        query = query.filter(or_(*[Source.tags.contains(tag) for tag in tag_list]))

    # Apply search filter (case-insensitive) on title and summary only
    # Content field excluded to avoid full table scan on large text columns
    escaped_q = escape_like_pattern(q)
    search_term = f"%{escaped_q}%"
    query = query.filter(
        Article.title.ilike(search_term)
        | Article.summary.ilike(search_term)
    )

    # Get total count
    total = query.count()

    # Get articles with pagination
    articles = (
        query.order_by(Article.published.desc().nullslast()).offset(offset).limit(limit).all()
    )

    return ArticleListResponse(
        items=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=ArticleListResponse)
def search_articles_post(
    q: str = Query(..., description="Search query"),
    sources: Optional[list[str]] = Query(None, description="List of source IDs"),
    tags: Optional[list[str]] = Query(None, description="List of tags"),
    limit: int = Query(10, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """
    Search articles (POST version).

    Same as GET but accepts lists for sources and tags.
    """
    # Start with base query
    query = db.query(Article).join(Source)

    # Filter by enabled sources
    query = query.filter(Source.enabled == True)

    # Filter by source IDs if provided
    if sources:
        query = query.filter(Article.source_id.in_(sources))

    # Filter by tags if provided
    if tags:
        for tag in tags:
            query = query.filter(Source.tags.contains(tag))

    # Apply search filter (case-insensitive) with SQL injection protection
    escaped_q = escape_like_pattern(q)
    search_term = f"%{escaped_q}%"
    query = query.filter(
        Article.title.ilike(search_term)
        | Article.summary.ilike(search_term)
        | Article.content.ilike(search_term)
    )

    # Get total count
    total = query.count()

    # Get articles with pagination
    articles = (
        query.order_by(Article.published.desc().nullslast()).offset(offset).limit(limit).all()
    )

    return ArticleListResponse(
        items=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        offset=offset,
        limit=limit,
    )
