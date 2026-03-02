"""MCP Prompts implementation.

This module provides pre-defined prompts for common RSS operations.
"""

from app.mcp.tools import mcp


@mcp.prompt()
def find_ai_news():
    """
    Prompt to find latest AI news.

    Use this when users ask about AI news or artificial intelligence updates.
    """
    return """Please help me find the latest AI news:

1. First, use list_sources to see available sources with AI or tech tags
2. Then use search_feeds with query="AI" or "人工智能" to find relevant articles
3. Return the top 5 most recent and relevant AI news items

For each article, provide:
- Title
- Source name
- Publication date
- A brief summary
"""


@mcp.prompt()
def tech_summary():
    """
    Prompt to summarize today's tech news.

    Use this when users want a summary of today's technology news.
    """
    return """Please help me summarize today's tech news:

1. Use list_sources to find sources with "tech" or "startup" tags
2. Use get_feed_items or search_feeds to get recent articles
3. Provide a summary of the top 5 most important tech stories

For each story, include:
- Title
- Source
- Why it's important (1-2 sentences)
"""


@mcp.prompt()
def explore_sources():
    """
    Prompt to explore available RSS sources.

    Use this to discover what RSS sources are available.
    """
    return """Please explore the available RSS sources:

1. Use list_sources to get all available sources
2. Group them by their tags (tech, news, AI, etc.)
3. Provide a summary of what topics/sources are available

This will help understand what information is accessible."""


@mcp.prompt()
def search_topic(topic: str):
    """
    Prompt to search for a specific topic.

    Args:
        topic: The topic to search for (e.g., "cryptocurrency", "climate", "Python")
    """
    return f"""Please help me find information about "{topic}":

1. Use search_feeds with query="{topic}" to find relevant articles
2. Also try related terms if needed
3. Return the most relevant and recent articles

Provide a brief summary of each found article."""
