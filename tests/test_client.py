"""MCP Test Client - Simulates LLM calling MCP service.

This module provides a test client for simulating LLM interactions with the MCP service.
It can be used to test and demonstrate how an LLM would interact with the RSS MCP service.
"""

import asyncio
import json
import sys
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPTestClient:
    """
    Test client for simulating LLM interactions with MCP service.

    This client connects to the MCP server and provides methods
    that simulate how an LLM would call the MCP tools.
    """

    def __init__(self, command: str = "uv", args: Optional[list[str]] = None):
        """
        Initialize the test client.

        Args:
            command: Command to run the MCP server (default: "uv")
            args: Arguments for the command (default: ["run", "rss-mcp"])
        """
        self.command = command
        self.args = args or ["run", "rss-mcp"]
        self.session: Optional[ClientSession] = None

    async def connect(self):
        """Connect to the MCP server."""
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
        )

        async with stdio_client(server_params) as (read, write):
            self.session = ClientSession(read, write)
            await self.session.initialize()

            # List available tools
            response = await self.session.list_tools()
            print(f"Connected to MCP server")
            print(f"Available tools: {[tool.name for tool in response.tools]}")

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.close()
            self.session = None

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool response as dictionary
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        result = await self.session.call_tool(tool_name, arguments)

        # Parse the result text
        if result.content:
            text_content = result.content[0].text
            return json.loads(text_content)

        return {}

    async def read_resource(self, uri: str) -> str:
        """
        Read an MCP resource.

        Args:
            uri: Resource URI to read

        Returns:
            Resource content as string
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        result = await self.session.read_resource(uri)

        if result.contents:
            return result.contents[0].text

        return ""

    # =========================================================================
    # LLM Simulation Methods
    # These methods simulate how an LLM would use the MCP tools
    # =========================================================================

    async def simulate_llm_list_sources(self) -> dict:
        """
        Simulate LLM calling list_sources.

        This is typically the first call an LLM would make to
        understand what RSS sources are available.
        """
        print("\n--- LLM Action: Listing all RSS sources ---")

        result = await self.call_tool("list_sources", {})

        print(f"Found {result.get('total', 0)} sources:")
        for source in result.get("sources", [])[:5]:
            print(f"  - {source['name']} (tags: {source.get('tags', [])})")

        return result

    async def simulate_llm_search_ai_news(self) -> dict:
        """
        Simulate LLM searching for AI news.

        This is how an LLM would search for specific content.
        """
        print("\n--- LLM Action: Searching for AI news ---")

        result = await self.call_tool(
            "search_feeds",
            {
                "query": "AI",
                "limit": 5,
            },
        )

        print(f"Found {result.get('total', 0)} articles")
        for item in result.get("items", [])[:5]:
            print(f"  - {item['title']}")
            print(f"    Source: {item.get('source_name')}")

        return result

    async def simulate_llm_get_source_items(self, source_id: str) -> dict:
        """
        Simulate LLM getting items from a specific source.

        Args:
            source_id: ID of the source to get items from
        """
        print(f"\n--- LLM Action: Getting items from source {source_id} ---")

        result = await self.call_tool(
            "get_feed_items",
            {
                "source_id": source_id,
                "limit": 5,
            },
        )

        print(f"Source: {result.get('source', {}).get('name')}")
        print(f"Found {result.get('total', 0)} articles")

        return result

    async def simulate_llm_add_source(self) -> dict:
        """
        Simulate LLM adding a new RSS source.
        """
        print("\n--- LLM Action: Adding a new RSS source ---")

        result = await self.call_tool(
            "add_source",
            {
                "url": "https://www.wired.com/feed/rss",
                "name": "Wired",
                "tags": "tech,science",
                "fetch_interval": 600,
            },
        )

        print(f"Result: {result.get('message', result)}")

        return result

    async def simulate_llm_full_workflow(self):
        """
        Simulate a complete LLM workflow.

        This demonstrates how an LLM would typically interact with
        the RSS MCP service to answer user questions.
        """
        print("\n" + "=" * 60)
        print("SIMULATING LLM WORKFLOW")
        print("=" * 60)

        # Step 1: List available sources
        print("\n[User Query]: What RSS sources do you have?")
        sources = await self.simulate_llm_list_sources()

        # Step 2: Search for specific topic
        print("\n[User Query]: Tell me about AI news")
        articles = await self.simulate_llm_search_ai_news()

        # Step 3: Get content from a specific article
        if articles.get("items"):
            first_article_id = articles["items"][0]["id"]
            print(f"\n[User Query]: Tell me more about the first article")
            content = await self.call_tool(
                "get_article_content",
                {
                    "article_id": first_article_id,
                },
            )
            print(f"Article content retrieved: {bool(content.get('article', {}).get('content'))}")

        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETE")
        print("=" * 60)


async def main():
    """Main entry point for the test client."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Test Client")
    parser.add_argument("--command", default="uv", help="Command to run MCP server")
    parser.add_argument("--workflow", action="store_true", help="Run full LLM workflow")
    parser.add_argument("--tool", help="Call a specific tool")
    parser.add_argument("--args", default="{}", help="Tool arguments as JSON")

    args = parser.parse_args()

    client = MCPTestClient(command=args.command)

    try:
        await client.connect()

        if args.workflow:
            await client.simulate_llm_full_workflow()
        elif args.tool:
            import json

            tool_args = json.loads(args.args)
            result = await client.call_tool(args.tool, tool_args)
            print(json.dumps(result, indent=2))
        else:
            # Interactive mode
            print("MCP Test Client")
            print("Commands:")
            print("  --workflow        Run full LLM workflow simulation")
            print("  --tool <name>     Call a specific tool")
            print("  --args <json>     Tool arguments")
            print("\nAvailable tools: list_sources, add_source, remove_source, ")
            print("                  enable_source, get_feed_items, search_feeds,")
            print("                  get_article_content, refresh_source, refresh_all")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
