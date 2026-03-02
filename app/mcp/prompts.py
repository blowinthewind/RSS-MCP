"""MCP Prompts implementation.

This module provides pre-defined prompts for common RSS operations.
Each prompt is designed to guide the LLM on how to use the MCP tools effectively.
"""

from app.mcp.tools import mcp


@mcp.prompt()
def find_ai_news():
    """Find latest AI news.

    Use when users ask about AI news or artificial intelligence updates.
    """
    return """Please help me find the latest AI news:

1. First, use list_sources to see available sources with AI or tech tags
2. Then use search_feeds with query="AI" or "人工智能" to find relevant articles
3. Return the top 5 most recent and relevant AI news items

For each article, provide:
- Title
- Source name
- Publication date
- A brief summary"""


@mcp.prompt()
def tech_summary():
    """Summarize today's tech news.

    Use when users want a summary of today's technology news.
    """
    return """Please help me summarize today's tech news:

1. Use list_sources to find sources with "tech" or "startup" tags
2. Use get_feed_items or search_feeds to get recent articles
3. Provide a summary of the top 5 most important tech stories

For each story, include:
- Title
- Source
- Why it's important (1-2 sentences)"""


@mcp.prompt()
def explore_sources():
    """Explore available RSS sources.

    Use to discover what RSS sources are available in the system.
    """
    return """Please explore the available RSS sources:

1. Use list_sources to get all available sources
2. Group them by their tags (tech, news, AI, cn, etc.)
3. Provide a summary of what topics/sources are available

This will help understand what information is accessible."""


@mcp.prompt()
def search_topic(topic: str):
    """Search for a specific topic.

    Args:
        topic: The topic to search for (e.g., "cryptocurrency", "climate", "Python")
    """
    return f"""Please help me find information about "{topic}":

1. Use search_feeds with query="{topic}" to find relevant articles
2. Also try related terms if needed
3. Return the most relevant and recent articles

Provide a brief summary of each found article."""


@mcp.prompt()
def add_rss_source(name: str, url: str, tags: str = ""):
    """Add a new RSS source.

    Args:
        name: The name of the RSS source
        url: The RSS feed URL
        tags: Comma-separated tags for categorization

    Use when users want to add a new RSS feed source.
    """
    return f"""Please help me add a new RSS source:

1. Use add_source tool with:
   - name: "{name}"
   - url: "{url}"
   - tags: "{tags}" (comma-separated, e.g., "tech,news")
   - fetch_interval: 300 (default, in seconds)

2. Verify the source was added successfully by checking the response

3. If successful, optionally use refresh_source to fetch initial articles"""


@mcp.prompt()
def remove_rss_source(source_id: str):
    """Remove an RSS source.

    Args:
        source_id: The ID of the source to remove

    Use when users want to remove an RSS feed source.
    """
    return f"""Please help me remove an RSS source:

1. First, use list_sources to find the source with id="{source_id}"
2. Use remove_source tool to delete it
3. Confirm the deletion was successful

Warning: This will also delete all articles from this source!"""


@mcp.prompt()
def toggle_source(source_id: str, enabled: bool):
    """Enable or disable an RSS source.

    Args:
        source_id: The ID of the source to toggle
        enabled: True to enable, False to disable

    Use when users want to enable or disable a specific RSS source.
    """
    action = "enable" if enabled else "disable"
    return f"""Please {action} an RSS source:

1. Use enable_source tool with:
   - source_id: "{source_id}"
   - enabled: {enabled}

2. Confirm the {action} was successful"""


@mcp.prompt()
def read_article(article_id: str):
    """Get full content of a specific article.

    Args:
        article_id: The ID of the article to read

    Use when users want to read the full content of a specific article.
    """
    return f"""Please get the full content of article "{article_id}":

1. Use get_article_content tool with article_id="{article_id}"
2. Return the full article content including:
   - Title
   - Source name
   - Full text content
   - Publication date"""


@mcp.prompt()
def refresh_feeds():
    """Refresh all RSS feeds.

    Use when users want to manually refresh all RSS feeds to get the latest articles.
    """
    return """Please refresh all RSS feeds:

1. Use refresh_all tool to fetch latest articles from all enabled sources
2. Report how many new articles were fetched
3. Provide a summary of the updated content"""


@mcp.prompt()
def refresh_single_source(source_id: str):
    """Refresh a single RSS source.

    Args:
        source_id: The ID of the source to refresh

    Use when users want to refresh a specific RSS source.
    """
    return f"""Please refresh RSS source "{source_id}":

1. Use refresh_source tool with source_id="{source_id}"
2. Report how many articles were fetched
3. Show the latest articles from this source"""


@mcp.prompt()
def get_source_articles(source_id: str, limit: int = 10):
    """Get articles from a specific source.

    Args:
        source_id: The ID of the source
        limit: Number of articles to return (default: 10)

    Use when users want to get articles from a specific RSS source.
    """
    return f"""Please get articles from source "{source_id}":

1. Use get_feed_items tool with:
   - source_id: "{source_id}"
   - limit: {limit}
   
2. Return the articles with:
   - Title
   - URL
   - Summary
   - Publication date"""


@mcp.prompt()
def custom_search(query: str, sources: str = "", tags: str = "", limit: int = 10):
    """Custom search across RSS feeds.

    Args:
        query: Search query
        sources: Optional comma-separated source IDs
        tags: Optional comma-separated tags to filter
        limit: Number of results (default: 10)

    Use for custom search queries.
    """
    sources_part = f"\n   - sources: {sources}" if sources else ""
    tags_part = f"\n   - tags: {tags}" if tags else ""
    return f"""Please search for "{query}":

1. Use search_feeds tool with:
   - query: "{query}"
   - limit: {limit}{sources_part}{tags_part}

2. Return the matching articles with:
   - Title
   - Source name
   - Summary
   - Publication date"""
