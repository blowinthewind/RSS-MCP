"""Configuration management for RSS MCP service.

This module provides centralized configuration management using Pydantic Settings.
Supports both environment variables and .env file configuration.
"""

import os
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils import split_by_comma


class Settings(BaseSettings):
    """
    Application settings for RSS MCP service.

    All settings can be configured via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database configuration
    # Connection URL for SQLAlchemy. Supports sqlite, postgresql, etc.
    # Example: "sqlite:///./rss.db" or "postgresql://user:pass@localhost/rss"
    database_url: str = Field(
        default="sqlite:///./rss.db",
        description="Database connection URL",
    )

    # Deployment mode: auto/stdio/sse
    # auto: automatically detect deployment mode
    # stdio: local stdio mode for MCP
    # sse: remote HTTP SSE mode
    deployment: Literal["auto", "stdio", "sse"] = Field(
        default="auto",
        description="Deployment mode: auto/stdio/sse",
    )

    # Server configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host for SSE mode",
    )
    port: int = Field(
        default=8000,
        description="Server port for SSE mode",
    )

    # Authentication configuration
    auth_enabled: bool = Field(
        default=False,
        description="Enable API key authentication for remote mode",
    )
    api_keys: str = Field(
        default="",
        description="Comma-separated list of allowed API keys for authentication",
    )
    
    @property
    def api_keys_list(self) -> list[str]:
        """Get API keys as a list."""
        return split_by_comma(self.api_keys)

    # RSS fetching configuration
    default_fetch_interval: int = Field(
        default=300,
        description="Default fetch interval in seconds",
    )
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds for fetching RSS feeds",
    )
    max_items_per_source: int = Field(
        default=50,
        description="Maximum number of items to fetch per source",
    )

    # Content extraction configuration
    enable_content_extraction: bool = Field(
        default=True,
        description="Enable content extraction with trafilatura",
    )

    # MCP server configuration
    mcp_name: str = Field(
        default="RSS Reader",
        description="MCP server name",
    )
    mcp_version: str = Field(
        default="0.1.0",
        description="MCP server version",
    )


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """
    Get database URL with proper path handling.

    For SQLite, converts relative paths to absolute paths.

    Returns:
        str: Processed database URL
    """
    url = settings.database_url

    # If using SQLite and path is relative, make it absolute
    if url.startswith("sqlite"):
        if ":/" not in url.replace("sqlite:///", ""):
            db_path = url.replace("sqlite:///", "")
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.getcwd(), db_path)
            url = f"sqlite:///{db_path}"

    return url
