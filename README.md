# RSS MCP Service

A MCP (Model Context Protocol) service for RSS feeds, designed for LLMs. Enables AI assistants to discover, search, and retrieve RSS feed content through a standardized MCP interface.

[中文文档](README_zh-CN.md) | English

## Features

- **MCP Protocol Support**: Full MCP implementation with Tools, Resources, and Prompts
- **Multi-client Compatibility**: Works with Claude Desktop, Cursor, Cherry Studio, Coze, and other MCP clients
- **Dual Deployment**: Auto-detects stdio (local) or SSE/Streamable HTTP (remote) mode
- **Preset RSS Sources**: Comes with built-in popular tech and news sources
- **Full CRUD Operations**: Add, remove, enable/disable RSS sources via MCP tools
- **Content Extraction**: Extracts full article content using trafilatura
- **Flexible Storage**: Supports SQLite (default) and PostgreSQL
- **Scheduled Fetching**: Automatic periodic RSS feed updates with configurable interval
- **Web UI**: Built-in web interface for managing sources, articles, API keys, and settings
- **Production Ready**: HTTPS support, API key authentication, production mode

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd RSS-MCP

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

#### Quick Start with Scripts

We provide convenient startup scripts for development:

```bash
# Terminal 1: Start backend
./start-backend.sh

# Terminal 2: Start frontend
./start-frontend.sh
```

The backend script will:
- Check for required dependencies (uv)
- Load environment variables from `.env` if present
- Start the server with SSE mode (default for debugging)

The frontend script will:
- Check for required dependencies (npm)
- Auto-install dependencies if needed
- Start the Vite dev server

#### Manual Start

```bash
# Run with uv (auto-detects mode)
uv run rss-mcp

# Or explicitly specify mode
DEPLOYMENT=stdio uv run rss-mcp              # Local stdio mode
DEPLOYMENT=sse uv run rss-mcp                # Remote SSE mode (legacy)
DEPLOYMENT=streamable-http uv run rss-mcp    # Remote Streamable HTTP mode (recommended)
```

### Configuration

The service can be configured via `config.yaml` or environment variables:

```yaml
# config.yaml
# Database configuration
database:
  url: "sqlite:///./rss.db"  # or "postgresql://user:pass@localhost/rss"

# Server configuration
server:
  host: "0.0.0.0"
  port: 8000

# Deployment mode: auto, stdio, sse, streamable-http
deployment: "auto"

# Security (enable for production)
security:
  production_mode: false  # Set to true for HTTPS redirect and stricter CORS

# Authentication
auth:
  enabled: false  # Set to true to require API keys

# RSS fetching configuration
rss:
  fetch_interval: 300        # seconds (5 minutes)
  request_timeout: 30        # seconds
  max_items_per_source: 50   # max articles per fetch
```

Environment variables override config file settings:
- `DATABASE_URL` - Database connection URL
- `DEPLOYMENT` - Deployment mode
- `AUTH_ENABLED` - Enable authentication
- `PRODUCTION_MODE` - Enable production mode
- `HOST` / `PORT` - Server binding

### Authentication (SSE/Streamable HTTP Mode)

When deploying in remote mode, you can enable API key authentication:

```bash
# Enable authentication
AUTH_ENABLED=true DEPLOYMENT=sse uv run rss-mcp

# Or with Streamable HTTP (recommended)
AUTH_ENABLED=true DEPLOYMENT=streamable-http uv run rss-mcp
```

**Managing API Keys:**

API keys are managed through the web UI at `http://localhost:8000`:

1. Open the web UI in your browser
2. Navigate to "API Keys" page
3. Click "Create API Key" to generate a new key
4. Copy the key immediately (shown only once)
5. Use the key in your MCP client

**Client Usage:**

```bash
# With curl
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/mcp

# In Cherry Studio SSE mode
# Add header: Authorization: Bearer your-api-key
```

**Note:** Authentication is only applied in SSE/Streamable HTTP mode. STDIO mode does not support authentication.

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

**STDIO Mode (Local):**

| Field | Value |
|-------|-------|
| Name | RSS Reader |
| Type | STDIO |
| Command | uv |
| Arguments | `--directory /path/to/RSS-MCP run rss-mcp` |

**Streamable HTTP Mode (Remote - Recommended):**

Start server first:
```bash
DEPLOYMENT=streamable-http uv run rss-mcp
```

Then configure:

| Field | Value |
|-------|-------|
| Type | Streamable HTTP |
| URL | http://localhost:8000/mcp |

**SSE Mode (Remote - Legacy):**

| Field | Value |
|-------|-------|
| Type | Server-Sent Events (SSE) |
| URL | http://localhost:8000/mcp |

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

**STDIO Mode (Local):**

```json
{
  "mcpServers": {
    "rss-reader": {
      "command": "uv",
      "args": ["--directory", "/path/to/RSS-MCP", "run", "rss-mcp"]
    }
  }
}
```

**Remote Mode (SSE):**

Start server first:
```bash
DEPLOYMENT=sse uv run rss-mcp
```

Then configure:
```json
{
  "mcpServers": {
    "rss-reader": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

**STDIO Mode (Local):**

```json
{
  "mcpServers": {
    "rss-reader": {
      "command": "uv",
      "args": ["--directory", "/path/to/RSS-MCP", "run", "rss-mcp"]
    }
  }
}
```

**Streamable HTTP Mode (Remote):**

Start server first:
```bash
DEPLOYMENT=streamable-http uv run rss-mcp
```

Then configure:
```json
{
  "mcpServers": {
    "rss-reader": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**SSE Mode (Remote - Legacy):**

```json
{
  "mcpServers": {
    "rss-reader": {
      "type": "sse",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Client Configuration Reference

| Client | STDIO | Streamable HTTP | SSE | Notes |
|--------|-------|-----------------|-----|-------|
| Cherry Studio | ✅ | ✅ | ✅ | All modes supported |
| Claude Desktop | ✅ | ✅ | ✅ | Use `type` field for remote modes |
| Cursor | ✅ | ❌ | ✅ | Cursor currently supports SSE only for remote |
| Windsurf | ✅ | ✅ | ✅ | Similar to Claude Desktop |

### Authentication in Clients

When authentication is enabled (`AUTH_ENABLED=true`), add the API key to your client configuration:

**Cherry Studio:**
Add header in the connection settings:
```
Authorization: Bearer your-api-key
```

**Claude Desktop:**
```json
{
  "mcpServers": {
    "rss-reader": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

**Cursor:**
Currently, Cursor does not support custom headers for MCP. Use a reverse proxy to add authentication, or disable authentication for Cursor usage.

## System Prompt

A system prompt template is provided in `SYSTEM_PROMPT.md` for LLM clients. This helps the AI understand when and how to use each MCP tool.

## Production Deployment

### Security Checklist

Before deploying to production:

- [ ] Enable `production_mode: true` in config.yaml (HTTPS redirect, strict CORS)
- [ ] Enable `auth.enabled: true` (require API key authentication)
- [ ] Generate API keys via Web UI and distribute to clients
- [ ] Use PostgreSQL instead of SQLite for better performance
- [ ] Set up reverse proxy (Nginx/Caddy) with HTTPS
- [ ] Configure firewall to restrict access

### Example Production Setup

**1. Update config.yaml:**

```yaml
security:
  production_mode: true

auth:
  enabled: true

database:
  url: "postgresql://user:password@localhost/rss"
```

**2. Use Caddy for automatic HTTPS:**

```
# Caddyfile
rss.example.com {
    reverse_proxy localhost:8000
}
```

**3. Start service:**

```bash
DEPLOYMENT=streamable-http uv run rss-mcp
```

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

## REST API & Web UI

When running in SSE or Streamable HTTP mode, REST API and Web UI are also available:

### REST API Endpoints

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
| `/api/api-keys` | GET | List API keys |
| `/api/api-keys` | POST | Create API key |
| `/api/api-keys/{id}` | DELETE | Delete API key |
| `/api/settings` | GET | Get settings |
| `/api/settings` | PATCH | Update settings |
| `/health` | GET | Health check |

### Web UI

Access the web UI at `http://localhost:8000` when running in remote mode:

- **Dashboard**: View statistics and overview
- **Sources**: Manage RSS sources
- **Articles**: Browse and search articles
- **API Keys**: Create and manage API keys
- **Settings**: Configure service settings (RSS fetch interval, etc.)

## Project Structure

```
RSS-MCP/
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
