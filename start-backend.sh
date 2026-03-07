#!/bin/bash
# Start backend server

set -e  # Exit on error

echo "Starting RSS MCP Backend..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv first."
    echo "Visit: https://github.com/astral-sh/uv"
    exit 1
fi

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "Loading environment from .env..."
    set -a
    source .env
    set +a
fi

# Default configuration
export DEPLOYMENT=${DEPLOYMENT:-streamable-http}
export AUTH_ENABLED=${AUTH_ENABLED:-false}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}

echo "Configuration:"
echo "  DEPLOYMENT: $DEPLOYMENT"
echo "  AUTH_ENABLED: $AUTH_ENABLED"
echo "  HOST: $HOST"
echo "  PORT: $PORT"

# Start the server
echo "Starting server..."
uv run rss-mcp
