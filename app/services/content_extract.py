"""Content extraction service.

This module provides content extraction functionality using trafilatura.
Extracts clean text content from HTML pages.
"""

import logging
from typing import Optional

import httpx
import trafilatura

from app.config import settings


logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Content Extractor.

    Extracts clean text content from HTML pages using trafilatura.
    """

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize content extractor.

        Args:
            timeout: Request timeout in seconds. Defaults to settings.request_timeout.
        """
        self.timeout = timeout or settings.request_timeout

    def extract(self, url: str) -> Optional[str]:
        """
        Extract content from a URL.

        Args:
            url: URL to extract content from

        Returns:
            Extracted text content, or None if extraction failed
        """
        if not settings.enable_content_extraction:
            return None

        try:
            logger.info(f"Extracting content from {url}")

            # Fetch HTML content
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                html_content = response.text

            # Extract content using trafilatura (markdown format for better readability)
            extracted = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                output_format="markdown",
            )

            if extracted:
                logger.info(f"Successfully extracted content from {url}")
                return extracted
            else:
                logger.warning(f"No content extracted from {url}")
                return None

        except httpx.TimeoutException:
            logger.error(f"Timeout while fetching {url}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None


def extract_content(url: str) -> Optional[str]:
    """
    Convenience function to extract content from a URL.

    Args:
        url: URL to extract content from

    Returns:
        Extracted text content, or None if extraction failed
    """
    extractor = ContentExtractor()
    return extractor.extract(url)
