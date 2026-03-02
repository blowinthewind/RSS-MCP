"""Feeds API routes.

This module provides API endpoints for fetching RSS feed items/articles.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source, Article
from app.schemas import ArticleResponse, ArticleListResponse
from app.services.content_extract import extract_content


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/feeds", tags=["feeds"])


@router.get("/{source_id}", response_model=ArticleListResponse)
def get_feed_items(
    source_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """
    Get articles from a specific RSS source.

    Returns paginated list of articles from the source.
    """
    # Check if source exists
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Get total count
    total = db.query(Article).filter(Article.source_id == source_id).count()

    # Get articles with pagination
    articles = (
        db.query(Article)
        .filter(Article.source_id == source_id)
        .order_by(Article.published.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return ArticleListResponse(
        items=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("", response_model=ArticleListResponse)
def get_all_feed_items(
    limit: int = Query(10, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    source_ids: Optional[str] = Query(None, description="Comma-separated source IDs"),
    db: Session = Depends(get_db),
):
    """
    Get articles from all enabled sources or specific sources.

    Returns paginated list of articles from specified sources.
    """
    query = db.query(Article)

    # Filter by source IDs if provided
    if source_ids:
        source_id_list = [s.strip() for s in source_ids.split(",")]
        query = query.filter(Article.source_id.in_(source_id_list))
    else:
        # Only get from enabled sources
        query = query.join(Source).filter(Source.enabled == True)

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
