# RSS MCP Service

A MCP (Model Context Protocol) service for RSS feeds, designed for LLMs. Enables AI assistants to discover, search, and retrieve RSS feed content through a standardized MCP interface.

## Features

- **MCP Protocol Support**: Full MCP implementation with Tools, Resources, and Prompts
- **Multi-client Compatibility**: Works with Claude Desktop, Cursor, Cherry Studio, Coze, and other MCP clients
- **Dual Deployment**: Auto-detects stdio (local) or SSE (remote) mode
- **Preset RSS Sources**: Comes with built-in popular tech and news sources
- **Full CRUD Operations**: Add, remove, enable/disable RSS sources via MCP tools
- **Content Extraction**: Extracts full article content using trafilatura
- **Flexible Storage**: Supports SQLite (default) and PostgreSQL
- **Scheduled Fetching**: Automatic periodic RSS feed updates with immediate first fetch

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd DailyNews

# Install dependencies using uv
uv venv
uv pip install -e .
```

### Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

### Running

```bash
# Run with uv (auto-detects mode)
uv run rss-mcp

# Or explicitly specify mode
DEPLOYMENT=stdio uv run rss-mcp  # Local stdio mode
DEPLOYMENT=sse uv run rss-mcp    # Remote SSE mode
```

### Docker Deployment

```bash
# Start with Docker Compose
docker-compose up -d
```

## MCP Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `list_sources` | tags, enabled | List all RSS sources with optional filtering |
| `add_source` | url, name, tags, fetch_interval | Add a new RSS source |
| `remove_source` | source_id | Remove an RSS source |
| `enable_source` | source_id, enabled | Enable or disable a source |
| `get_feed_items` | source_id, limit, offset | Get articles from a specific source |
| `search_feeds` | query, sources, tags, limit | Search articles across sources |
| `get_article_content` | article_id | Get full content of an article |
| `refresh_source` | source_id | Manually refresh a specific source |
| `refresh_all` | - | Refresh all enabled sources |

## MCP Resources

| Resource | Description |
|----------|-------------|
| `sources://list` | All RSS sources as JSON |
| `sources://by-tag/{tag}` | Sources filtered by tag |
| `feed://{source_id}/latest` | Latest articles from a source |
| `config://settings` | Current configuration |

## MCP Prompts

| Prompt | Description |
|--------|-------------|
| `find_ai_news` | Find latest AI news |
| `tech_summary` | Summarize today's tech news |
| `explore_sources` | Explore available RSS sources |
| `search_topic` | Search for a specific topic |
| `add_rss_source` | Add a new RSS source |
| `remove_rss_source` | Remove an RSS source |
| `toggle_source` | Enable/disable a source |
| `read_article` | Get full article content |
| `refresh_feeds` | Refresh all RSS feeds |
| `refresh_single_source` | Refresh a single source |
| `get_source_articles` | Get articles from a source |
| `custom_search` | Custom search query |

## Preset RSS Sources

The service comes with 8 preset RSS sources:

| Source | Tags |
|--------|------|
| Bloomberg Technology-AI | tech, ai |
| Politico Technology News | tech, ai |
| 财新科技频道 | tech, cn |
| 财新最新 | world, finance, cn |
| V2ex | tech, cn, community |
| BBC World | news, world |
| MIT Technology Review | tech, ai |
| Ars Technica | tech |

## Client Configuration

### Cherry Studio (Recommended)

1. Open Cherry Studio → Settings → MCP Servers
2. Click "Add Server"
3. Configure:

| Field | Value |
|-------|-------|
| Name | RSS Reader |
| Type | STDIO |
| Command | uv |
| Arguments | `--directory /path/to/DailyNews run rss-mcp` |

Or use SSE mode (start server first with `DEPLOYMENT=sse uv run rss-mcp`):

| Field | Value |
|-------|-------|
| Type | Server-Sent Events (SSE) |
| URL | http://localhost:8000/sse |

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rss-reader": {
      "command": "uv",
      "args": ["run", "rss-mcp"]
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
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## System Prompt

A system prompt template is provided in `SYSTEM_PROMPT.md` for LLM clients. This helps the AI understand when and how to use each MCP tool.

## Testing

### Run Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_api.py -v
```

### MCP Test Client

Test MCP tools directly:

```bash
# List available tools
uv run python tests/test_client.py --list

# Call a specific tool
uv run python tests/test_client.py --tool list_sources
uv run python tests/test_client.py --tool search_feeds --args '{"query":"AI","limit":5}'
uv run python tests/test_client.py --tool refresh_all
```

### MCP Inspector

Debug MCP server with visual inspector:

```bash
npx @modelcontextprotocol/inspector uv run rss-mcp
```

Then open http://localhost:6274 in your browser.

## REST API

When running in SSE mode, REST API is also available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sources` | GET | List all sources |
| `/api/sources` | POST | Add a new source |
| `/api/sources/{id}` | GET | Get source details |
| `/api/sources/{id}` | PATCH | Update source |
| `/api/sources/{id}` | DELETE | Delete source |
| `/api/feeds/{source_id}` | GET | Get articles from source |
| `/api/search?q=query` | GET | Search articles |
| `/api/articles/{id}` | GET | Get article details |
| `/health` | GET | Health check |

## Project Structure

```
DailyNews/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── database.py         # Database connection
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── main.py            # Application entry point
│   ├── routers/           # REST API routes
│   │   ├── sources.py
│   │   ├── feeds.py
│   │   ├── search.py
│   │   └── articles.py
│   ├── services/          # Business logic
│   │   ├── rss_fetcher.py
│   │   ├── content_extract.py
│   │   ├── scheduler.py
│   │   └── preset_loader.py
│   └── mcp/              # MCP implementation
│       ├── tools.py
│       ├── resources.py
│       └── prompts.py
├── presets/
│   └── sources.json       # Preset RSS sources
├── tests/
│   ├── test_services.py   # Unit tests
│   ├── test_api.py       # REST API tests
│   └── test_client.py    # MCP test client
├── SYSTEM_PROMPT.md      # System prompt template
├── pyproject.toml
└── docker-compose.yml
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run linter
uv run ruff check .

# Type checking
uv run mypy app/
```

## License

MIT License
