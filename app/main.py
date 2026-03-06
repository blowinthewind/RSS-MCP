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
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import init_db, get_db
from app.models import Source, Article
from app.mcp.tools import mcp
from app.services.scheduler import start_scheduler, stop_scheduler
from app.routers import sources_router, feeds_router, search_router, articles_router, api_keys_router, settings_router
from app.routers.api_keys import verify_api_key, verify_api_key_from_header


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
    # For SSE mode, we need to handle MCP lifespan differently
    if settings.deployment in ["sse", "auto"]:
        mcp_app = mcp.http_app()
        # Use MCP's lifespan which handles both MCP and our lifespan
        app_lifespan = mcp_app.lifespan
    else:
        app_lifespan = lifespan

    app = FastAPI(
        title="RSS MCP Service",
        description="A MCP service for RSS feeds, designed for LLMs",
        version=settings.mcp_version,
        lifespan=app_lifespan,
    )

    # Add CORS middleware for MCP Inspector and frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(sources_router)
    app.include_router(feeds_router)
    app.include_router(search_router)
    app.include_router(articles_router)
    app.include_router(api_keys_router)
    app.include_router(settings_router)

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
    # Note: Must use mount() to properly handle lifespan events
    if settings.deployment in ["sse", "auto"]:
        # Mount at root - http_app() already has /mcp route
        app.mount("/", mcp_app)

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

    # Setup MCP resources and prompts before creating app
    setup_mcp_resources()
    setup_mcp_prompts()

    # Create the FastAPI app with all routers
    app = create_app()

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

        # Use shared verification function
        is_valid, error_message = verify_api_key_from_header(auth_header)
        if not is_valid:
            return JSONResponse(status_code=401, content={"error": error_message})

        return await call_next(request)

    # Run with uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)


class AuthMiddleware:
    """ASGI middleware for API key authentication."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Only process HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Skip auth if not enabled
        if not settings.auth_enabled:
            await self.app(scope, receive, send)
            return

        # Get request path
        path = scope.get("path", "")

        # Skip auth for health and root endpoints
        if path in ["/health", "/"]:
            await self.app(scope, receive, send)
            return

        # Get headers
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode("utf-8")

        # Use shared verification function
        is_valid, error_message = verify_api_key_from_header(auth_header)
        if not is_valid:
            await self._send_error(send, 401, error_message)
            return

        await self.app(scope, receive, send)

    async def _send_error(self, send, status_code: int, message: str):
        """Send error response."""
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [(b"content-type", b"application/json")],
        })
        import json
        await send({
            "type": "http.response.body",
            "body": json.dumps({"error": message}).encode(),
        })


def run_streamable_http():
    """
    Run MCP server in Streamable HTTP mode.

    This is the recommended mode for remote MCP connections.
    Uses standard HTTP with streaming support for better compatibility.
    Supports optional API key authentication.
    """
    import asyncio

    # Setup MCP resources and prompts
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

    # Run MCP server with streamable-http transport
    logger.info(f"Starting MCP server in streamable-http mode on {settings.host}:{settings.port}...")

    async def start_server():
        await mcp.run_http_async(
            transport="streamable-http",
            host=settings.host,
            port=settings.port,
            middleware=[AuthMiddleware],
        )

    asyncio.run(start_server())


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
    elif deployment == "streamable-http":
        run_streamable_http()
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
