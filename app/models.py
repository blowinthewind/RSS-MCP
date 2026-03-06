"""Database models for RSS MCP service.

Defines SQLAlchemy ORM models for Source and Article entities.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def generate_id() -> str:
    """Generate a unique ID using UUID4."""
    return uuid.uuid4().hex[:12]


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class Source(Base):
    """
    RSS Source model.

    Represents an RSS/Atom feed source with its configuration and metadata.
    """

    __tablename__ = "sources"

    # Primary key - unique identifier
    id: Mapped[str] = mapped_column(
        String(12),
        primary_key=True,
        default=generate_id,
    )

    # Source name
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # RSS feed URL
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    # Tags for categorization - stored as JSON list
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: [],
    )

    # Whether this source is active - indexed for filtering
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )

    # Fetch interval in seconds
    fetch_interval: Mapped[int] = mapped_column(
        Integer,
        default=300,
    )

    # Last fetch timestamp
    last_fetched: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )

    # Last update timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )

    # Relationship to articles
    articles: Mapped[list["Article"]] = relationship(
        "Article",
        back_populates="source",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name={self.name})>"


class Article(Base):
    """
    Article model.

    Represents an article/item from an RSS feed.
    """

    __tablename__ = "articles"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(12),
        primary_key=True,
        default=generate_id,
    )

    # Foreign key to source - indexed for filtering and joins
    source_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("sources.id"),
        nullable=False,
        index=True,
    )

    # Article title
    title: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    # Original article URL - indexed for deduplication checks
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        index=True,
    )

    # Article summary/description
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Full content extracted from article
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Article author
    author: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Publication timestamp - indexed for sorting
    published: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    # When this article was fetched
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )

    # Relationship to source
    source: Mapped["Source"] = relationship(
        "Source",
        back_populates="articles",
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title={self.title[:50]}...)>"


class ApiKey(Base):
    """
    API Key model.

    Represents an API key for authentication.
    Keys are stored as SHA256 hashes for security.
    """

    __tablename__ = "api_keys"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(12),
        primary_key=True,
        default=generate_id,
    )

    # Key name (user-defined)
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # SHA256 hash of the API key (never store plain text)
    key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,  # Index for fast lookup during authentication
    )

    # Preview of the key (first 4 + **** + last 4 chars) for display
    key_preview: Mapped[str] = mapped_column(
        String(13),
        nullable=False,
    )

    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
    )

    # Last usage timestamp
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Whether this key is active
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name}, preview={self.key_preview})>"


class SystemConfig(Base):
    """
    System configuration model.

    Stores dynamic system configuration in key-value format.
    """

    __tablename__ = "system_config"

    # Configuration key
    key: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    # Configuration value
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Last update timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )

    def __repr__(self) -> str:
        return f"<SystemConfig(key={self.key}, value={self.value[:50]}...)>"

    @classmethod
    def get_value(cls, db, key: str, default: str = "") -> str:
        """Get configuration value by key."""
        config = db.query(cls).filter(cls.key == key).first()
        return config.value if config else default

    @classmethod
    def set_value(cls, db, key: str, value: str) -> "SystemConfig":
        """Set configuration value by key."""
        config = db.query(cls).filter(cls.key == key).first()
        if config:
            config.value = value
        else:
            config = cls(key=key, value=value)
            db.add(config)
        db.commit()
        return config
