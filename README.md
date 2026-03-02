# RSS MCP Service

A MCP (Model Context Protocol) service for RSS feeds, designed for LLMs. Enables AI assistants to discover, search, and retrieve RSS feed content through a standardized MCP interface.

## Features

- **MCP Protocol Support**: Full MCP implementation with Tools, Resources, and Prompts
- **Multi-client Compatibility**: Works with Claude Desktop, Cursor, Coze, and other MCP clients
- **Dual Deployment**: Supports both stdio (local) and SSE (remote) modes
- **Preset RSS Sources**: Comes with built-in popular tech and news sources
- **Full CRUD Operations**: Add, remove, enable/disable RSS sources via MCP tools
- **Content Extraction**: Extracts full article content using trafilatura
- **Flexible Storage**: Supports SQLite (default) and PostgreSQL
- **Scheduled Fetching**: Automatic periodic RSS feed updates

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd rss-mcp

# Install dependencies
pip install -e .
```

### Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

### Running

```bash
# Run in auto mode (detects stdio or SSE)
python -m app.main

# Or explicitly specify mode
DEPLOYMENT=stdio python -m app.main  # Local mode
DEPLOYMENT=sse python -m app.main   # Remote mode
```

### Docker Deployment

```bash
# Start with Docker Compose
docker-compose up -d
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_sources` | List all RSS sources with optional filtering |
| `add_source` | Add a new RSS source |
| `remove_source` | Remove an RSS source |
| `enable_source` | Enable or disable a source |
| `get_feed_items` | Get articles from a specific source |
| `search_feeds` | Search articles across sources |
| `get_article_content` | Get full content of an article |
| `refresh_source` | Manually refresh a source |
| `refresh_all` | Refresh all enabled sources |

## MCP Resources

| Resource | Description |
|----------|-------------|
| `sources://list` | All RSS sources as JSON |
| `sources://by-tag/{tag}` | Sources filtered by tag |
| `feed://{source_id}/latest` | Latest articles from a source |
| `config://settings` | Current configuration |

## MCP Prompts

- `find_ai_news`: Find latest AI news
- `tech_summary`: Summarize today's tech news
- `explore_sources`: Explore available RSS sources
- `search_topic`: Search for a specific topic

## API Endpoints

When running in SSE mode, REST API is also available:

- `GET /api/sources` - List all sources
- `POST /api/sources` - Add a new source
- `GET /api/feeds/{source_id}` - Get articles from a source
- `GET /api/search?q=query` - Search articles

## Client Configuration

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rss-reader": {
      "command": "python",
      "args": ["-m", "app.main"]
    }
  }
}
```

### Cursor

Add to Cursor settings (MCP configuration):

```json
{
  "mcpServers": {
    "rss-reader": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .
```

## License

MIT License
