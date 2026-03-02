#!/usr/bin/env python
"""Simple test script for MCP stdio mode.

This script tests the MCP server by spawning it as a subprocess and
communicating via JSON-RPC over stdio.

Usage:
    python tests/test_stdio.py
"""

import subprocess
import json
import sys


def send_json_rpc(request: dict) -> dict:
    """Send a JSON-RPC request and return the response."""
    # Write request to stdin
    json_line = json.dumps(request) + "\n"
    return json_line


def main():
    """Run stdio MCP test."""
    print("Starting MCP server test...", file=sys.stderr)

    # Start the MCP server as a subprocess
    proc = subprocess.Popen(
        ["uv", "run", "rss-mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    print("Server started, sending initialize request...", file=sys.stderr)

    # Send initialize request
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    proc.stdin.write(json.dumps(initialize_request) + "\n")
    proc.stdin.flush()

    # Read response
    response = proc.stdout.readline()
    print(f"Initialize response: {response[:200]}...", file=sys.stderr)

    # Send initialized notification
    initialized_notification = {"jsonrpc": "2.0", "method": "initialized", "params": {}}
    proc.stdin.write(json.dumps(initialized_notification) + "\n")
    proc.stdin.flush()

    # Send tools/list request
    list_tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    proc.stdin.write(json.dumps(list_tools_request) + "\n")
    proc.stdin.flush()

    # Read tools list
    response = proc.stdout.readline()
    print(f"Tools list response: {response[:500]}...", file=sys.stderr)

    # Clean up
    proc.terminate()
    proc.wait()

    print("Test complete!", file=sys.stderr)


if __name__ == "__main__":
    main()
