"""Utility functions for the application.

This module provides common utility functions used across the application.
"""


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
