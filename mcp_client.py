"""
Model Context Protocol (MCP) Client and Integration Manager.
Handles connecting to Pipedream MCP servers (YouTube, Google Drive, Notion)
via streamable HTTP / SSE transports, inspecting available tools, and executing MCP tool calls.
"""

import asyncio
from typing import Dict, List, Optional, Any
from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPManager:
    """Manages connections, tool introspection, and status tracking for MCP servers."""

    @staticmethod
    def build_tools_config(
        youtube_url: Optional[str] = None,
        drive_url: Optional[str] = None,
        notion_url: Optional[str] = None
    ) -> Dict[str, Dict[str, str]]:
        """Constructs MCP connection definitions dictionary for MultiServerMCPClient."""
        config: Dict[str, Dict[str, str]] = {}
        if youtube_url and youtube_url.strip():
            config["youtube"] = {
                "url": youtube_url.strip(),
                "transport": "streamable_http"
            }
        if drive_url and drive_url.strip():
            config["drive"] = {
                "url": drive_url.strip(),
                "transport": "streamable_http"
            }
        if notion_url and notion_url.strip():
            config["notion"] = {
                "url": notion_url.strip(),
                "transport": "streamable_http"
            }
        return config

    @classmethod
    async def test_server_connection(cls, name: str, url: str, timeout_seconds: float = 8.0) -> Dict[str, Any]:
        """
        Tests connection to an individual Pipedream MCP server endpoint.
        Introspects available tools and reports real server status.
        """
        if not url or not url.strip():
            return {
                "server": name,
                "status": "unconfigured",
                "message": "URL not provided",
                "tools": []
            }

        tools_config = {
            name: {
                "url": url.strip(),
                "transport": "streamable_http"
            }
        }

        try:
            client = MultiServerMCPClient(tools_config)
            # Query server with timeout to avoid hanging if endpoint is unreachable
            tools = await asyncio.wait_for(client.get_tools(), timeout=timeout_seconds)
            tool_names = [getattr(t, "name", str(t)) for t in tools]
            tool_descriptions = [getattr(t, "description", "") for t in tools]
            
            return {
                "server": name,
                "status": "connected",
                "message": f"Successfully connected! Found {len(tool_names)} tool(s).",
                "tools": tool_names,
                "descriptions": tool_descriptions
            }
        except asyncio.TimeoutError:
            return {
                "server": name,
                "status": "timeout",
                "message": f"Connection timed out after {timeout_seconds}s. Verify the endpoint URL and Pipedream permissions.",
                "tools": []
            }
        except Exception as exc:
            return {
                "server": name,
                "status": "error",
                "message": f"Connection failed: {str(exc)}",
                "tools": []
            }

    @classmethod
    def test_server_connection_sync(cls, name: str, url: str) -> Dict[str, Any]:
        """Synchronous wrapper for test_server_connection."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(cls.test_server_connection(name, url))
            finally:
                loop.close()
        except Exception as e:
            return {
                "server": name,
                "status": "error",
                "message": f"Unexpected error during connection test: {str(e)}",
                "tools": []
            }

    @classmethod
    async def get_all_configured_tools(
        cls,
        youtube_url: Optional[str] = None,
        drive_url: Optional[str] = None,
        notion_url: Optional[str] = None
    ) -> List[Any]:
        """Returns instantiated LangChain tools from all active MCP server endpoints."""
        config = cls.build_tools_config(youtube_url, drive_url, notion_url)
        if not config:
            return []
        
        client = MultiServerMCPClient(config)
        return await client.get_tools()
