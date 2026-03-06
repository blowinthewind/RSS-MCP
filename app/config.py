"""Configuration management for RSS MCP service.

This module provides centralized configuration management using Pydantic Settings.
Supports YAML config file, environment variables, and .env file configuration.
Priority: Environment variables > .env file > config.yaml > defaults
"""

import os
from typing import Literal, Optional
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default config file path
CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"


def load_yaml_config() -> dict:
    """Load configuration from YAML file if it exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config.yaml: {e}")
    return {}


# Load YAML config
_yaml_config = load_yaml_config()


def get_yaml_value(key_path: str, default=None):
    """
    Get value from YAML config using dot notation.
    
    Args:
        key_path: Dot-separated path (e.g., "database.url")
        default: Default value if not found
    
    Returns:
        Value from config or default
    """
    keys = key_path.split(".")
    value = _yaml_config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


class Settings(BaseSettings):
    """
    Application settings for RSS MCP service.

    Configuration priority (highest to lowest):
    1. Environment variables
    2. .env file
    3. config.yaml file
    4. Default values
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database configuration
    database_url: str = Field(
        default_factory=lambda: get_yaml_value("database.url", "sqlite:///./rss.db"),
        description="Database connection URL",
    )

    # Deployment mode: auto/stdio/sse
    deployment: Literal["auto", "stdio", "sse"] = Field(
        default_factory=lambda: get_yaml_value("deployment", "auto"),
        description="Deployment mode: auto/stdio/sse",
    )

    # Server configuration
    host: str = Field(
        default_factory=lambda: get_yaml_value("server.host", "0.0.0.0"),
        description="Server host for SSE mode",
    )
    port: int = Field(
        default_factory=lambda: get_yaml_value("server.port", 8000),
        description="Server port for SSE mode",
    )

    # Authentication configuration
    auth_enabled: bool = Field(
        default_factory=lambda: get_yaml_value("auth.enabled", False),
        description="Enable API key authentication for remote mode",
    )

    # RSS fetching configuration
    default_fetch_interval: int = Field(
        default_factory=lambda: get_yaml_value("rss.fetch_interval", 300),
        description="Default fetch interval in seconds",
    )
    request_timeout: int = Field(
        default_factory=lambda: get_yaml_value("rss.request_timeout", 30),
        description="Request timeout in seconds for fetching RSS feeds",
    )
    max_items_per_source: int = Field(
        default_factory=lambda: get_yaml_value("rss.max_items_per_source", 50),
        description="Maximum number of items to fetch per source",
    )

    # Content extraction configuration
    enable_content_extraction: bool = Field(
        default_factory=lambda: get_yaml_value("content.extraction_enabled", True),
        description="Enable content extraction with trafilatura",
    )

    # MCP server configuration
    mcp_name: str = Field(
        default_factory=lambda: get_yaml_value("mcp.name", "RSS Reader"),
        description="MCP server name",
    )
    mcp_version: str = Field(
        default_factory=lambda: get_yaml_value("mcp.version", "0.1.0"),
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
