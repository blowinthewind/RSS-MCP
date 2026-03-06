"""Utility functions for the application.

This module provides common utility functions used across the application.
"""

import socket
from typing import Optional
from urllib.parse import urlparse

import safehttpx


def split_by_comma(text: str | None) -> list[str]:
    """
    Split text by comma (both English and Chinese).

    Handles both English comma (,) and Chinese comma (，).
    Also handles full-width comma commonly used in Chinese text.

    Args:
        text: Input text to split. Can be None or empty string.

    Returns:
        List of stripped, non-empty strings.

    Examples:
        >>> split_by_comma("a, b, c")
        ['a', 'b', 'c']
        >>> split_by_comma("标签1，标签2，标签3")
        ['标签1', '标签2', '标签3']
        >>> split_by_comma("mixed，english, 中文")
        ['mixed', 'english', '中文']
        >>> split_by_comma(None)
        []
        >>> split_by_comma("")
        []
    """
    if not text:
        return []

    # Replace Chinese comma (，) and other variants with English comma
    # 中文逗号：，（U+FF0C 全角逗号）
    normalized = text.replace("，", ",")

    # Split and filter empty strings
    return [t.strip() for t in normalized.split(",") if t.strip()]


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate URL format and prevent SSRF attacks.

    This function validates:
    - URL format (scheme, netloc)
    - Scheme is http/https
    - Domain is valid
    - Hostname does not resolve to internal IP (SSRF protection)

    Args:
        url: URL string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    url = url.strip()

    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format: must include scheme (http/https) and domain"

        if result.scheme not in ["http", "https"]:
            return False, f"Invalid URL scheme: {result.scheme}. Only http and https are allowed"

        # Basic domain validation
        domain = result.netloc.lower()
        if not domain or "." not in domain:
            return False, "Invalid domain in URL"

        # SSRF protection: validate hostname does not resolve to internal IP
        hostname = result.hostname
        if not hostname:
            return False, "Invalid hostname in URL"

        # Block localhost
        if hostname.lower() in ['localhost', 'localhost.localdomain', '127.0.0.1', '::1']:
            return False, "URL cannot use localhost"

        # Set DNS resolution timeout to prevent long waits
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(3)  # 3 second timeout

        try:
            # Use getaddrinfo to support both IPv4 and IPv6
            addr_info = socket.getaddrinfo(hostname, None)
            if not addr_info:
                return False, "Could not resolve hostname"

            # Get the first resolved IP address
            ip = addr_info[0][4][0]

            # Verify it's a public IP (not internal)
            if not safehttpx.is_public_ip(ip):
                return False, f"URL resolves to internal IP address: {ip}"
        except socket.timeout:
            return False, "DNS resolution timeout"
        except socket.gaierror:
            # DNS resolution failed, might be a new domain
            # Allow it to proceed (will fail later if truly invalid)
            pass
        finally:
            # Restore original timeout
            socket.setdefaulttimeout(old_timeout)

        return True, ""
    except Exception as e:
        return False, f"URL validation error: {str(e)}"
