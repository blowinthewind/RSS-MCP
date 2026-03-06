"""Tests for configuration management."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from app.config import Settings, get_database_url, settings


class TestSettings:
    """Test cases for Settings class."""

    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.database_url == "sqlite:///./rss.db"
            assert settings.deployment == "auto"
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000
            assert settings.auth_enabled is False
            assert settings.default_fetch_interval == 300
            assert settings.request_timeout == 30
            assert settings.max_items_per_source == 50
            assert settings.enable_content_extraction is True
            assert settings.mcp_name == "RSS Reader"
            assert settings.mcp_version == "0.1.0"

    def test_custom_values_from_env(self):
        """Test loading custom values from environment variables."""
        env_vars = {
            "DATABASE_URL": "postgresql://user:pass@localhost/rss",
            "DEPLOYMENT": "sse",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "AUTH_ENABLED": "true",
            "DEFAULT_FETCH_INTERVAL": "600",
            "REQUEST_TIMEOUT": "60",
            "MAX_ITEMS_PER_SOURCE": "100",
            "ENABLE_CONTENT_EXTRACTION": "false",
            "MCP_NAME": "Custom RSS",
            "MCP_VERSION": "1.0.0",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.database_url == "postgresql://user:pass@localhost/rss"
            assert settings.deployment == "sse"
            assert settings.host == "127.0.0.1"
            assert settings.port == 9000
            assert settings.auth_enabled is True
            assert settings.default_fetch_interval == 600
            assert settings.request_timeout == 60
            assert settings.max_items_per_source == 100
            assert settings.enable_content_extraction is False
            assert settings.mcp_name == "Custom RSS"
            assert settings.mcp_version == "1.0.0"

    def test_deployment_literal_validation(self):
        """Test that deployment field only accepts valid values."""
        # Valid values
        for value in ["auto", "stdio", "sse", "streamable-http"]:
            with patch.dict(os.environ, {"DEPLOYMENT": value}, clear=True):
                settings = Settings()
                assert settings.deployment == value

        # Invalid value should raise validation error
        with patch.dict(os.environ, {"DEPLOYMENT": "invalid"}, clear=True):
            with pytest.raises(Exception):
                Settings()


class TestGetDatabaseUrl:
    """Test cases for get_database_url function."""

    def test_postgresql_url_unchanged(self):
        """Test PostgreSQL URL is returned unchanged."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost/rss"}, clear=True):
            settings = Settings()
            with patch('app.config.settings', settings):
                result = get_database_url()
                assert result == "postgresql://user:pass@localhost/rss"

    def test_sqlite_absolute_path_unchanged(self):
        """Test SQLite with absolute path is returned unchanged."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:////absolute/path/to/rss.db"}, clear=True):
            settings = Settings()
            with patch('app.config.settings', settings):
                result = get_database_url()
                assert result == "sqlite:////absolute/path/to/rss.db"

    def test_sqlite_relative_path_converted(self):
        """Test SQLite with relative path is converted to absolute."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./rss.db"}, clear=True):
            settings = Settings()
            with patch('app.config.settings', settings):
                with patch('os.path.isabs', return_value=False):
                    with patch('os.path.join', return_value='/current/dir/rss.db'):
                        result = get_database_url()
                        assert result == "sqlite:////current/dir/rss.db"

    def test_sqlite_url_with_special_chars(self):
        """Test SQLite URL handling with special characters."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./my-database_v1.db"}, clear=True):
            settings = Settings()
            with patch('app.config.settings', settings):
                result = get_database_url()
                assert result.startswith("sqlite:///")


class TestGlobalSettings:
    """Test cases for global settings instance."""

    def test_global_settings_exists(self):
        """Test that global settings instance exists."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_global_settings_singleton(self):
        """Test that global settings behaves as singleton."""
        # Import again should return same instance
        from app.config import settings as settings2
        assert settings is settings2
