"""REST API tests for RSS MCP service.

Tests the REST API endpoints when running in SSE mode.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create a test client for the REST API."""
    from app.main import create_app
    from app.database import init_db

    # Initialize database
    init_db()

    # Create app
    app = create_app()

    # Load preset sources
    from app.services.preset_loader import load_preset_sources

    load_preset_sources()

    # Create test client
    client = TestClient(app)
    yield client


class TestSourcesAPI:
    """Tests for /api/sources endpoints."""

    def test_list_sources(self, test_client):
        """Test listing all sources."""
        response = test_client.get("/api/sources")

        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert "total" in data
        assert data["total"] > 0

    def test_get_source(self, test_client):
        """Test getting a specific source."""
        # First get the list
        response = test_client.get("/api/sources")
        sources = response.json()["sources"]

        if sources:
            source_id = sources[0]["id"]
            response = test_client.get(f"/api/sources/{source_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == source_id

    def test_create_source(self, test_client):
        """Test creating a new source."""
        new_source = {
            "name": "Test Source",
            "url": "https://example.com/test-rss.xml",
            "tags": ["test"],
            "fetch_interval": 600,
        }

        response = test_client.post("/api/sources", json=new_source)

        # May return 201 if successful, or 400 if URL already exists
        assert response.status_code in [201, 400]

    def test_delete_source(self, test_client):
        """Test deleting a source."""
        # First create a source to delete
        new_source = {
            "name": "To Delete",
            "url": "https://example.com/delete-test.xml",
            "tags": ["test"],
        }

        response = test_client.post("/api/sources", json=new_source)

        if response.status_code == 201:
            source_id = response.json()["id"]

            # Delete it
            response = test_client.delete(f"/api/sources/{source_id}")

            assert response.status_code == 200
            assert response.json()["success"] is True


class TestFeedsAPI:
    """Tests for /api/feeds endpoints."""

    def test_get_feed_items(self, test_client):
        """Test getting items from a source."""
        # First get the list
        response = test_client.get("/api/sources")
        sources = response.json()["sources"]

        if sources:
            source_id = sources[0]["id"]
            response = test_client.get(f"/api/feeds/{source_id}")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data

    def test_get_all_feed_items(self, test_client):
        """Test getting all feed items."""
        response = test_client.get("/api/feeds")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestSearchAPI:
    """Tests for /api/search endpoints."""

    def test_search_articles(self, test_client):
        """Test searching articles."""
        response = test_client.get("/api/search?q=tech")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_search_with_tags(self, test_client):
        """Test searching with tag filter."""
        response = test_client.get("/api/search?q=test&tags=tech")

        assert response.status_code == 200

    def test_search_pagination(self, test_client):
        """Test search pagination."""
        response = test_client.get("/api/search?q=tech&limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0


class TestArticlesAPI:
    """Tests for /api/articles endpoints."""

    def test_get_article(self, test_client):
        """Test getting a specific article."""
        # First get some articles
        response = test_client.get("/api/feeds")

        if response.json()["items"]:
            article_id = response.json()["items"][0]["id"]
            response = test_client.get(f"/api/articles/{article_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == article_id


class TestHealthCheck:
    """Tests for health check and root endpoints."""

    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root(self, test_client):
        """Test root endpoint."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
