"""Articles API routes.

This module provides API endpoints for individual article operations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Article
from app.schemas import ArticleResponse, OperationResponse
from app.services.content_extract import extract_content


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: str,
    include_content: bool = Query(False, description="Include full content"),
    db: Session = Depends(get_db),
):
    """
    Get a specific article by ID.

    Optionally extracts full content if not already stored.
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Extract content if requested and not already present
    if include_content and not article.content:
        try:
            content = extract_content(article.url)
            if content:
                article.content = content
                db.commit()
        except Exception as e:
            logger.warning(f"Failed to extract content: {e}")

    return ArticleResponse.model_validate(article)


@router.post("/{article_id}/extract", response_model=OperationResponse)
def extract_article_content(
    article_id: str,
    db: Session = Depends(get_db),
):
    """
    Extract and store full content for an article.
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if article.content:
        return OperationResponse(
            success=True,
            message="Content already exists",
            data={"content_length": len(article.content)},
        )

    try:
        content = extract_content(article.url)
        if content:
            article.content = content
            db.commit()
            return OperationResponse(
                success=True,
                message="Content extracted successfully",
                data={"content_length": len(content)},
            )
        else:
            return OperationResponse(
                success=False,
                message="Failed to extract content",
            )
    except Exception as e:
        logger.error(f"Error extracting content: {e}")
        return OperationResponse(
            success=False,
            message=f"Error: {str(e)}",
        )
