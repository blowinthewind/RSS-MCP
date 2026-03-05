"""Pydantic schemas for request/response validation.

This module defines Pydantic models for API request and response validation,
including source and article schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Source Schemas
# =============================================================================


class SourceBase(BaseModel):
    """Base schema for Source with common fields."""

    name: str = Field(..., description="Source name")
    url: str = Field(..., description="RSS feed URL")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    fetch_interval: int = Field(default=300, description="Fetch interval in seconds")


class SourceCreate(SourceBase):
    """Schema for creating a new Source."""

    pass


class SourceUpdate(BaseModel):
    """Schema for updating an existing Source."""

    name: Optional[str] = Field(None, description="Source name")
    url: Optional[str] = Field(None, description="RSS feed URL")
    tags: Optional[list[str]] = Field(None, description="Tags for categorization")
    fetch_interval: Optional[int] = Field(None, description="Fetch interval in seconds")
    enabled: Optional[bool] = Field(None, description="Whether source is enabled")


class SourceResponse(SourceBase):
    """Schema for Source response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique identifier")
    enabled: bool = Field(..., description="Whether source is enabled")
    last_fetched: Optional[datetime] = Field(None, description="Last fetch timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    article_count: int = Field(0, description="Number of articles from this source")


class SourceListResponse(BaseModel):
    """Schema for list of sources response."""

    sources: list[SourceResponse] = Field(..., description="List of sources")
    total: int = Field(..., description="Total count")


# =============================================================================
# Article Schemas
# =============================================================================


class ArticleBase(BaseModel):
    """Base schema for Article with common fields."""

    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")


class ArticleResponse(BaseModel):
    """Schema for Article response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique identifier")
    source_id: str = Field(..., description="Source ID")
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    summary: Optional[str] = Field(None, description="Article summary")
    content: Optional[str] = Field(None, description="Full article content")
    author: Optional[str] = Field(None, description="Article author")
    published: Optional[datetime] = Field(None, description="Publication timestamp")
    fetched_at: datetime = Field(..., description="Fetch timestamp")


class ArticleListResponse(BaseModel):
    """Schema for list of articles response."""

    items: list[ArticleResponse] = Field(..., description="List of articles")
    total: int = Field(..., description="Total count")
    offset: int = Field(..., description="Offset for pagination")
    limit: int = Field(..., description="Limit for pagination")


# =============================================================================
# Search Schemas
# =============================================================================


class SearchRequest(BaseModel):
    """Schema for search request."""

    query: str = Field(..., description="Search query")
    sources: Optional[list[str]] = Field(None, description="Source IDs to search")
    tags: Optional[list[str]] = Field(None, description="Tags to filter")
    limit: int = Field(default=10, description="Maximum results to return")
    offset: int = Field(default=0, description="Offset for pagination")


class SearchResponse(BaseModel):
    """Schema for search response."""

    items: list[ArticleResponse] = Field(..., description="Search results")
    total: int = Field(..., description="Total matching count")
    query: str = Field(..., description="Search query used")


# =============================================================================
# Operation Response Schemas
# =============================================================================


class OperationResponse(BaseModel):
    """Generic response for operations."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation message")
    data: Optional[dict] = Field(None, description="Additional data")


# =============================================================================
# Configuration Schemas
# =============================================================================


class ConfigResponse(BaseModel):
    """Schema for configuration response."""

    mcp_name: str = Field(..., description="MCP server name")
    mcp_version: str = Field(..., description="MCP server version")
    deployment: str = Field(..., description="Deployment mode")
    auth_enabled: bool = Field(..., description="Authentication enabled")
    total_sources: int = Field(..., description="Total number of sources")
    total_articles: int = Field(..., description="Total number of articles")
