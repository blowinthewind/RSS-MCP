"""Source management API routes.

This module provides API endpoints for RSS source management.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source, Article
from app.schemas import (
    SourceCreate,
    SourceUpdate,
    SourceResponse,
    SourceListResponse,
    OperationResponse,
)


logger = logging.getLogger(__name__)


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
from app.services.rss_fetcher import fetch_feed
from app.services.content_extract import extract_content


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=SourceListResponse)
def list_sources(
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: Session = Depends(get_db),
):
    """
    List all RSS sources.

    Supports filtering by tags and enabled status.
    """
    query = db.query(Source)

    # Apply filters
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for tag in tag_list:
            query = query.filter(Source.tags.contains(tag))

    if enabled is not None:
        query = query.filter(Source.enabled == enabled)

    sources = query.order_by(Source.created_at.desc()).all()

    return SourceListResponse(
        sources=[SourceResponse.model_validate(s) for s in sources],
        total=len(sources),
    )


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: str, db: Session = Depends(get_db)):
    """
    Get a specific RSS source by ID.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return SourceResponse.model_validate(source)


@router.post("", response_model=SourceResponse, status_code=201)
def create_source(source_data: SourceCreate, db: Session = Depends(get_db)):
    """
    Add a new RSS source.
    """
    # Validate URL format
    is_valid, error_msg = validate_url(source_data.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Check if URL already exists
    existing = db.query(Source).filter(Source.url == source_data.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source with this URL already exists")

    # Create new source
    source = Source(
        name=source_data.name,
        url=source_data.url,
        tags=source_data.tags,
        fetch_interval=source_data.fetch_interval,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    # Optionally fetch initial articles
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

    return SourceResponse.model_validate(source)


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: str,
    source_data: SourceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing RSS source.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Update fields
    if source_data.name is not None:
        source.name = source_data.name
    if source_data.url is not None:
        source.url = source_data.url
    if source_data.tags is not None:
        source.tags = source_data.tags
    if source_data.fetch_interval is not None:
        source.fetch_interval = source_data.fetch_interval
    if source_data.enabled is not None:
        source.enabled = source_data.enabled

    db.commit()
    db.refresh(source)

    return SourceResponse.model_validate(source)


@router.delete("/{source_id}", response_model=OperationResponse)
def delete_source(source_id: str, db: Session = Depends(get_db)):
    """
    Delete an RSS source and its articles.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Delete source (articles are cascade deleted)
    db.delete(source)
    db.commit()

    return OperationResponse(
        success=True,
        message=f"Source {source_id} deleted successfully",
    )


@router.post("/{source_id}/enable", response_model=OperationResponse)
def enable_source(
    source_id: str,
    enabled: bool = Query(True, description="Enable or disable source"),
    db: Session = Depends(get_db),
):
    """
    Enable or disable an RSS source.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source.enabled = enabled
    db.commit()

    return OperationResponse(
        success=True,
        message=f"Source {source_id} {'enabled' if enabled else 'disabled'}",
    )


@router.post("/{source_id}/refresh", response_model=OperationResponse)
def refresh_source(source_id: str, db: Session = Depends(get_db)):
    """
    Manually refresh an RSS source.
    """
    from app.services.scheduler import refresh_source as do_refresh

    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    success = do_refresh(source_id)

    if success:
        return OperationResponse(
            success=True,
            message=f"Source {source_id} refreshed successfully",
        )
    else:
        return OperationResponse(
            success=False,
            message=f"Failed to refresh source {source_id}",
        )
