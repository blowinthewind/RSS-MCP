# RSS MCP 服务

一个为 LLM 设计的 RSS MCP（模型上下文协议）服务。使 AI 助手能够通过标准化的 MCP 接口发现、搜索和检索 RSS 订阅源内容。

中文 | [English](README.md)

## 功能特性

- **MCP 协议支持**：完整的 MCP 实现，包含工具、资源和提示词
- **多客户端兼容**：支持 Claude Desktop、Cursor、Cherry Studio、Coze 等 MCP 客户端
- **双模式部署**：自动检测 stdio（本地）或 SSE/Streamable HTTP（远程）模式
- **预设 RSS 源**：内置热门科技新闻源
- **完整 CRUD 操作**：通过 MCP 工具添加、删除、启用/禁用 RSS 源
- **内容提取**：使用 trafilatura 提取完整文章内容
- **灵活存储**：支持 SQLite（默认）和 PostgreSQL
- **定时抓取**：自动定期更新 RSS 订阅源，可配置抓取间隔
- **Web 界面**：内置 Web 界面，用于管理订阅源、文章、API 密钥和设置
- **生产就绪**：支持 HTTPS、API 密钥认证、生产模式

## 快速开始

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd RSS-MCP

# 使用 uv 安装依赖
uv venv
uv pip install -e .
```

### 配置

复制 `.env.example` 到 `.env` 并自定义配置：

```bash
cp .env.example .env
```

### 运行

#### 使用脚本快速启动

我们提供便捷的启动脚本用于开发：

```bash
# 终端 1：启动后端
./start-backend.sh

# 终端 2：启动前端
./start-frontend.sh
```

后端脚本将：
- 检查必需的依赖（uv）
- 加载 `.env` 中的环境变量（如果存在）
- 以 SSE 模式启动服务器（调试默认）

前端脚本将：
- 检查必需的依赖（npm）
- 如需则自动安装依赖
- 启动 Vite 开发服务器

#### 手动启动

```bash
# 使用 uv 运行（自动检测模式）
uv run rss-mcp

# 或显式指定模式
DEPLOYMENT=stdio uv run rss-mcp              # 本地 stdio 模式
DEPLOYMENT=sse uv run rss-mcp                # 远程 SSE 模式（旧版）
DEPLOYMENT=streamable-http uv run rss-mcp    # 远程 Streamable HTTP 模式（推荐）
```

### 配置说明

服务可通过 `config.yaml` 或环境变量配置：

```yaml
# config.yaml
# 数据库配置
database:
  url: "sqlite:///./rss.db"  # 或 "postgresql://user:pass@localhost/rss"

# 服务器配置
server:
  host: "0.0.0.0"
  port: 8000

# 部署模式：auto, stdio, sse, streamable-http
deployment: "auto"

# 安全配置（生产环境启用）
security:
  production_mode: false  # 设为 true 启用 HTTPS 重定向和严格 CORS

# 认证配置
auth:
  enabled: false  # 设为 true 需要 API 密钥

# RSS 抓取配置
rss:
  fetch_interval: 300        # 秒（5 分钟）
  request_timeout: 30        # 秒
  max_items_per_source: 50   # 每次抓取最大文章数
```

环境变量会覆盖配置文件设置：
- `DATABASE_URL` - 数据库连接 URL
- `DEPLOYMENT` - 部署模式
- `AUTH_ENABLED` - 启用认证
- `PRODUCTION_MODE` - 启用生产模式
- `HOST` / `PORT` - 服务器绑定地址

### 认证（SSE/Streamable HTTP 模式）

在远程模式下部署时，可以启用 API 密钥认证：

```bash
# 启用认证
AUTH_ENABLED=true DEPLOYMENT=sse uv run rss-mcp

# 或使用 Streamable HTTP（推荐）
AUTH_ENABLED=true DEPLOYMENT=streamable-http uv run rss-mcp
```

**管理 API 密钥：**

API 密钥通过 Web 界面在 `http://localhost:8000` 管理：

1. 在浏览器中打开 Web 界面
2. 导航到"API 密钥"页面
3. 点击"创建 API 密钥"生成新密钥
4. 立即复制密钥（仅显示一次）
5. 在 MCP 客户端中使用该密钥

**客户端使用：**

```bash
# 使用 curl
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/mcp

# 在 Cherry Studio SSE 模式中
# 添加请求头：Authorization: Bearer your-api-key
```

**注意：** 认证仅在 SSE/Streamable HTTP 模式下生效。STDIO 模式不支持认证。

### Docker 部署

```bash
# 使用 Docker Compose 启动
docker-compose up -d
```

## MCP 工具

| 工具 | 参数 | 描述 |
|------|------------|-------------|
| `list_sources` | tags, enabled | 列出所有 RSS 源，支持可选过滤 |
| `add_source` | url, name, tags, fetch_interval | 添加新的 RSS 源 |
| `remove_source` | source_id | 删除 RSS 源 |
| `enable_source` | source_id, enabled | 启用或禁用源 |
| `get_feed_items` | source_id, limit, offset | 从特定源获取文章 |
| `search_feeds` | query, sources, tags, limit | 跨源搜索文章 |
| `get_article_content` | article_id | 获取文章完整内容 |
| `refresh_source` | source_id | 手动刷新特定源 |
| `refresh_all` | - | 刷新所有启用的源 |

## MCP 资源

| 资源 | 描述 |
|----------|-------------|
| `sources://list` | 所有 RSS 源的 JSON 格式 |
| `sources://by-tag/{tag}` | 按标签过滤的源 |
| `feed://{source_id}/latest` | 源的最新文章 |
| `config://settings` | 当前配置 |

## MCP 提示词

| 提示词 | 描述 |
|--------|-------------|
| `find_ai_news` | 查找最新 AI 新闻 |
| `tech_summary` | 总结今日科技新闻 |
| `explore_sources` | 探索可用的 RSS 源 |
| `search_topic` | 搜索特定主题 |
| `add_rss_source` | 添加新的 RSS 源 |
| `remove_rss_source` | 删除 RSS 源 |
| `toggle_source` | 启用/禁用源 |
| `read_article` | 获取文章完整内容 |
| `refresh_feeds` | 刷新所有 RSS 订阅源 |
| `refresh_single_source` | 刷新单个源 |
| `get_source_articles` | 从源获取文章 |
| `custom_search` | 自定义搜索查询 |

## 预设 RSS 源

服务自带 8 个预设 RSS 源：

| 源 | 标签 |
|--------|------|
| Bloomberg Technology-AI | tech, ai |
| Politico Technology News | tech, ai |
| 财新科技频道 | tech, cn |
| 财新最新 | world, finance, cn |
| V2ex | tech, cn, community |
| BBC World | news, world |
| MIT Technology Review | tech, ai |
| Ars Technica | tech |

## 客户端配置

### Cherry Studio（推荐）

1. 打开 Cherry Studio → 设置 → MCP 服务器
2. 点击"添加服务器"
3. 配置：

**STDIO 模式（本地）：**

| 字段 | 值 |
|-------|-------|
| 名称 | RSS Reader |
| 类型 | STDIO |
| 命令 | uv |
| 参数 | `--directory /path/to/RSS-MCP run rss-mcp` |

**Streamable HTTP 模式（远程 - 推荐）：**

先启动服务器：
```bash
DEPLOYMENT=streamable-http uv run rss-mcp
```

然后配置：

| 字段 | 值 |
|-------|-------|
| 类型 | Streamable HTTP |
| URL | http://localhost:8000/mcp |

**SSE 模式（远程 - 旧版）：**

| 字段 | 值 |
|-------|-------|
| 类型 | Server-Sent Events (SSE) |
| URL | http://localhost:8000/mcp |

### Claude Desktop

添加到 `claude_desktop_config.json`：

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

添加到 Cursor 设置（MCP 配置）：

**STDIO 模式（本地）：**

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

**远程模式（SSE）：**

先启动服务器：
```bash
DEPLOYMENT=sse uv run rss-mcp
```

然后配置：
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

添加到 `claude_desktop_config.json`：

**STDIO 模式（本地）：**

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

**Streamable HTTP 模式（远程）：**

先启动服务器：
```bash
DEPLOYMENT=streamable-http uv run rss-mcp
```

然后配置：
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

**SSE 模式（远程 - 旧版）：**

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

### 客户端配置参考

| 客户端 | STDIO | Streamable HTTP | SSE | 说明 |
|--------|-------|-----------------|-----|-------|
| Cherry Studio | ✅ | ✅ | ✅ | 支持所有模式 |
| Claude Desktop | ✅ | ✅ | ✅ | 远程模式使用 `type` 字段 |
| Cursor | ✅ | ❌ | ✅ | Cursor 远程仅支持 SSE |
| Windsurf | ✅ | ✅ | ✅ | 类似 Claude Desktop |

### 客户端认证配置

当启用认证（`AUTH_ENABLED=true`）时，在客户端配置中添加 API 密钥：

**Cherry Studio：**
在连接设置中添加请求头：
```
Authorization: Bearer your-api-key
```

**Claude Desktop：**
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

**Cursor：**
目前 Cursor 不支持 MCP 的自定义请求头。使用反向代理添加认证，或禁用 Cursor 的认证。

## 系统提示词

`SYSTEM_PROMPT.md` 中提供了系统提示词模板供 LLM 客户端使用。帮助 AI 理解何时以及如何使用每个 MCP 工具。

## 生产部署

### 安全清单

生产部署前：

- [ ] 在 config.yaml 中启用 `production_mode: true`（HTTPS 重定向、严格 CORS）
- [ ] 启用 `auth.enabled: true`（需要 API 密钥认证）
- [ ] 通过 Web UI 生成 API 密钥并分发给客户端
- [ ] 使用 PostgreSQL 替代 SQLite 以获得更好性能
- [ ] 设置反向代理（Nginx/Caddy）并启用 HTTPS
- [ ] 配置防火墙限制访问

### 生产环境配置示例

**1. 更新 config.yaml：**

```yaml
security:
  production_mode: true

auth:
  enabled: true

database:
  url: "postgresql://user:password@localhost/rss"
```

**2. 使用 Caddy 自动 HTTPS：**

```
# Caddyfile
rss.example.com {
    reverse_proxy localhost:8000
}
```

**3. 启动服务：**

```bash
DEPLOYMENT=streamable-http uv run rss-mcp
```

## 测试

### 运行测试

```bash
# 所有测试
uv run pytest tests/ -v

# 特定测试文件
uv run pytest tests/test_api.py -v
```

### MCP 测试客户端

直接测试 MCP 工具：

```bash
# 列出可用工具
uv run python tests/test_client.py --list

# 调用特定工具
uv run python tests/test_client.py --tool list_sources
uv run python tests/test_client.py --tool search_feeds --args '{"query":"AI","limit":5}'
uv run python tests/test_client.py --tool refresh_all
```

### MCP Inspector

使用可视化检查器调试 MCP 服务器：

```bash
npx @modelcontextprotocol/inspector uv run rss-mcp
```

然后在浏览器中打开 http://localhost:6274。

## REST API 和 Web 界面

在 SSE 或 Streamable HTTP 模式下运行时，REST API 和 Web 界面也可用：

### REST API 端点

| 端点 | 方法 | 描述 |
|----------|--------|-------------|
| `/api/sources` | GET | 列出所有源 |
| `/api/sources` | POST | 添加新源 |
| `/api/sources/{id}` | GET | 获取源详情 |
| `/api/sources/{id}` | PATCH | 更新源 |
| `/api/sources/{id}` | DELETE | 删除源 |
| `/api/feeds/{source_id}` | GET | 从源获取文章 |
| `/api/search?q=query` | GET | 搜索文章 |
| `/api/articles/{id}` | GET | 获取文章详情 |
| `/api/api-keys` | GET | 列出 API 密钥 |
| `/api/api-keys` | POST | 创建 API 密钥 |
| `/api/api-keys/{id}` | DELETE | 删除 API 密钥 |
| `/api/settings` | GET | 获取设置 |
| `/api/settings` | PATCH | 更新设置 |
| `/health` | GET | 健康检查 |

### Web 界面

在远程模式下运行时，访问 `http://localhost:8000` 打开 Web 界面：

- **仪表板**：查看统计和概览
- **源**：管理 RSS 源
- **文章**：浏览和搜索文章
- **API 密钥**：创建和管理 API 密钥
- **设置**：配置服务设置（RSS 抓取间隔等）

## 项目结构

```
RSS-MCP/
├── app/
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库连接
│   ├── models.py          # SQLAlchemy 模型
│   ├── schemas.py         # Pydantic 模式
│   ├── main.py            # 应用入口
│   ├── routers/           # REST API 路由
│   │   ├── sources.py
│   │   ├── feeds.py
│   │   ├── search.py
│   │   └── articles.py
│   ├── services/          # 业务逻辑
│   │   ├── rss_fetcher.py
│   │   ├── content_extract.py
│   │   ├── scheduler.py
│   │   └── preset_loader.py
│   └── mcp/              # MCP 实现
│       ├── tools.py
│       ├── resources.py
│       └── prompts.py
├── presets/
│   └── sources.json       # 预设 RSS 源
├── tests/
│   ├── test_services.py   # 单元测试
│   ├── test_api.py       # REST API 测试
│   └── test_client.py    # MCP 测试客户端
├── SYSTEM_PROMPT.md      # 系统提示词模板
├── pyproject.toml
└── docker-compose.yml
```

## 开发

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行代码检查
uv run ruff check .

# 类型检查
uv run mypy app/
```

## 许可证

MIT 许可证
