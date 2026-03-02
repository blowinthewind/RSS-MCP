"""Main application entry point.

This module provides the main application setup for both stdio and SSE modes.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
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

    # Start scheduler
    try:
        start_scheduler()
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
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # Create app
    app = create_app()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount MCP at /mcp
    mcp_server = mcp.stream_app()
    app.mount("/mcp", mcp_server)

    # Run server
    import uvicorn

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
