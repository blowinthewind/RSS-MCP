"""Authentication middleware for SSE mode.

This module provides API key authentication for SSE deployments.
"""

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


logger = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Checks for valid API key in Authorization header for SSE endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        """Process the request and validate API key if required."""
        # Skip authentication if not enabled
        if not settings.auth_enabled:
            return await call_next(request)

        # Skip authentication for health check
        if request.url.path in ["/health", "/"]:
            return await call_next(request)

        # Check API key
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            logger.warning(f"Missing Authorization header from {request.client.host}")
            return JSONResponse(
                status_code=401,
                content={"error": "Missing Authorization header"},
            )

        # Extract API key from "Bearer <key>" format
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Invalid Authorization format from {request.client.host}")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid Authorization header format. Use: Bearer <api_key>"},
            )

        api_key = parts[1]

        # Validate API key
        if api_key not in settings.api_keys_list:
            logger.warning(f"Invalid API key from {request.client.host}")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"},
            )

        # API key is valid, proceed with request
        return await call_next(request)


def check_api_key(api_key: Optional[str]) -> bool:
    """
    Check if API key is valid.

    Args:
        api_key: API key to validate

    Returns:
        True if valid, False otherwise
    """
    if not settings.auth_enabled:
        return True

    if not api_key:
        return False

    return api_key in settings.api_keys_list
