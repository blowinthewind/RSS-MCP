"""Main application entry point.

This module provides the main application setup for both stdio and SSE modes.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import init_db, get_db
from app.models import Source, Article
from app.mcp.tools import mcp
from app.services.scheduler import start_scheduler, stop_scheduler
from app.routers import sources_router, feeds_router, search_router, articles_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_mcp_resources():
    """
    Setup MCP resources.

    Registers resource handlers with the MCP server.
    """
    from app.mcp import resources as mcp_resources

    # Register sources list resource
    @mcp.resource("sources://list")
    def sources_list():
        """Get list of all RSS sources."""
        return mcp_resources.get_sources_list()

    # Register sources by tag resource
    @mcp.resource("sources://by-tag/{tag}")
    def sources_by_tag(tag: str):
        """Get sources filtered by tag."""
        return mcp_resources.get_sources_by_tag(tag)

    # Register feed latest resource
    @mcp.resource("feed://{source_id}/latest")
    def feed_latest(source_id: str, limit: int = 10):
        """Get latest articles from a source."""
        return mcp_resources.get_feed_latest(source_id, limit)

    # Register config resource
    @mcp.resource("config://settings")
    def config_settings():
        """Get current configuration."""
        return mcp_resources.get_config()


def setup_mcp_prompts():
    """
    Setup MCP prompts.

    Imports prompts to register them with the MCP server.
    """
    from app.mcp import prompts as mcp_prompts  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting RSS MCP Service...")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Import and load preset sources
    try:
        from app.services.preset_loader import load_preset_sources

        load_preset_sources()
    except Exception as e:
        logger.warning(f"Failed to load preset sources: {e}")

    # Start scheduler (without initial fetch to avoid blocking)
    try:
        from app.services.scheduler import scheduler

        scheduler.start(run_immediately=False)
    except Exception as e:
        logger.warning(f"Failed to start scheduler: {e}")

    logger.info(f"RSS MCP Service started in {settings.deployment} mode")

    yield

    # Shutdown
    logger.info("Shutting down RSS MCP Service...")
    stop_scheduler()
    logger.info("RSS MCP Service stopped")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="RSS MCP Service",
        description="A MCP service for RSS feeds, designed for LLMs",
        version=settings.mcp_version,
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(sources_router)
    app.include_router(feeds_router)
    app.include_router(search_router)
    app.include_router(articles_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "service": "rss-mcp"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with service info."""
        return {
            "service": "RSS MCP Service",
            "version": settings.mcp_version,
            "mcp_endpoint": "/mcp" if settings.deployment in ["auto", "sse"] else None,
        }

    # Stats endpoint for frontend
    @app.get("/api/stats")
    async def get_stats(db: Session = Depends(get_db)):
        """Get service statistics for frontend."""
        total_sources = db.query(Source).count()
        total_articles = db.query(Article).count()

        return {
            "mcp_name": "RSS MCP Service",
            "mcp_version": settings.mcp_version,
            "deployment": settings.deployment,
            "auth_enabled": settings.auth_enabled,
            "total_sources": total_sources,
            "total_articles": total_articles,
        }

    # Mount MCP HTTP app for SSE mode
    if settings.deployment in ["sse", "auto"]:
        mcp_app = mcp.http_app()
        app.mount("/mcp", mcp_app)

    return app


def run_stdio():
    """
    Run MCP server in stdio mode.

    This is used for local MCP client connections.
    """
    # Setup MCP
    setup_mcp_resources()
    setup_mcp_prompts()

    # Initialize database
    init_db()

    # Load preset sources
    try:
        from app.services.preset_loader import load_preset_sources

        load_preset_sources()
    except Exception as e:
        logger.warning(f"Failed to load preset sources: {e}")

    # Run MCP server
    logger.info("Starting MCP server in stdio mode...")
    mcp.run(transport="stdio")


def run_sse():
    """
    Run MCP server in SSE mode.

    This is used for remote MCP client connections.
    Supports optional API key authentication.
    Uses the FastAPI app with both REST API and MCP endpoints.
    """
    from starlette.responses import JSONResponse
    import uvicorn

    # Create the FastAPI app with all routers
    app = create_app()

    # Get the MCP HTTP app and mount it
    mcp_app = mcp.http_app()

    @app.middleware("http")
    async def add_auth_middleware(request, call_next):
        """Add authentication to MCP endpoints."""
        # Skip auth if not enabled
        if not settings.auth_enabled:
            return await call_next(request)

        # Skip auth for health, root, and API routes
        if request.url.path in ["/health", "/"] or request.url.path.startswith("/api"):
            return await call_next(request)

        # Check API key for /mcp and other paths
        auth_header = request.headers.get("authorization", "")

        if not auth_header:
            return JSONResponse(status_code=401, content={"error": "Missing Authorization header"})

        # Extract Bearer token
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid Authorization header format. Use: Bearer <api_key>"},
            )

        api_key = parts[1]
        if api_key not in settings.api_keys_list:
            return JSONResponse(status_code=401, content={"error": "Invalid API key"})

        return await call_next(request)

    # Run with uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)


def main():
    """
    Main entry point.

    Determines deployment mode and runs appropriate server.
    """
    deployment = settings.deployment.lower()

    if deployment == "stdio":
        run_stdio()
    elif deployment == "sse":
        run_sse()
    elif deployment == "auto":
        # Auto-detect: check if running in a terminal
        if sys.stdin.isatty():
            run_sse()
        else:
            run_stdio()
    else:
        logger.error(f"Unknown deployment mode: {deployment}")
        sys.exit(1)


if __name__ == "__main__":
    main()
