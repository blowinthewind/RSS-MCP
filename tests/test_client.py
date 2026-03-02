#!/usr/bin/env python
"""MCP Test Client - Tests MCP service via subprocess.

This module provides a simple test client that communicates with MCP
via stdio using subprocess. Works for both stdio and SSE modes.

Usage:
    # SSE mode (recommended):
    # Terminal 1: DEPLOYMENT=sse uv run rss-mcp
    # Terminal 2: uv run python tests/test_client.py

    # Stdio mode:
    # uv run python tests/test_client.py --mode stdio
"""

import subprocess
import json
import sys
import os
from typing import Any, Optional


class MCPTestClient:
    """Simple MCP test client using subprocess."""

    def __init__(
        self,
        mode: str = "stdio",
        sse_url: str = "http://localhost:8000/sse",
    ):
        self.mode = mode
        self.sse_url = sse_url
        self.proc: Optional[subprocess.Popen] = None
        self._request_id = 1

    def start(self):
        """Start the MCP server process."""
        if self.mode == "stdio":
            self.proc = subprocess.Popen(
                ["uv", "run", "rss-mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            # Send initialize
            self._send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            )
            # Read initialize response
            self._read_response()
            # Send initialized notification
            self._send_notification("initialized", {})
        else:
            raise RuntimeError("SSE mode not supported in subprocess mode")

    def _send_request(self, method: str, params: dict) -> int:
        """Send a JSON-RPC request."""
        request = {"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params}
        self._request_id += 1
        self.proc.stdin.write(json.dumps(request) + "\n")
        self.proc.stdin.flush()
        return self._request_id - 1

    def _send_notification(self, method: str, params: dict):
        """Send a JSON-RPC notification (no response expected)."""
        request = {"jsonrpc": "2.0", "method": method, "params": params}
        self.proc.stdin.write(json.dumps(request) + "\n")
        self.proc.stdin.flush()

    def _read_response(self) -> dict:
        """Read a JSON-RPC response."""
        line = self.proc.stdout.readline()
        return json.loads(line)

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        """Call an MCP tool."""
        if not self.proc:
            raise RuntimeError("Client not started")

        req_id = self._send_request("tools/call", {"name": tool_name, "arguments": arguments})

        # Read response
        response = self._read_response()

        if "result" in response:
            result = response["result"]
            # Handle different response formats
            if isinstance(result, dict):
                if "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        text_content = content[0].get("text", str(content[0]))
                        try:
                            return json.loads(text_content)
                        except (json.JSONDecodeError, AttributeError):
                            return {"raw": text_content}
                return result

        return response

    def list_tools(self) -> list:
        """List available tools."""
        if not self.proc:
            raise RuntimeError("Client not started")

        req_id = self._send_request("tools/list", {})
        response = self._read_response()

        if "result" in response and "tools" in response["result"]:
            return response["result"]["tools"]
        return []

    def stop(self):
        """Stop the MCP server process."""
        if self.proc:
            self.proc.terminate()
            self.proc.wait()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Test Client")
    parser.add_argument("--mode", default="stdio", choices=["stdio"])
    parser.add_argument("--tool", help="Tool to call")
    parser.add_argument("--args", default="{}", help="Tool arguments as JSON")
    parser.add_argument("--list", action="store_true", help="List available tools")

    args = parser.parse_args()

    client = MCPTestClient(mode=args.mode)

    try:
        print("Starting MCP server...", file=sys.stderr)
        client.start()

        if args.list:
            tools = client.list_tools()
            print(json.dumps([t["name"] for t in tools], indent=2))
        elif args.tool:
            tool_args = json.loads(args.args)
            result = client.call_tool(args.tool, tool_args)
            print(json.dumps(result, indent=2))
        else:
            tools = client.list_tools()
            print("Available tools:", file=sys.stderr)
            for tool in tools:
                print(f"  - {tool['name']}", file=sys.stderr)

    finally:
        client.stop()


if __name__ == "__main__":
    main()
