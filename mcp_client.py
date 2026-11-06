"""
Model Context Protocol (MCP) client.

Two jobs:
  1. Health checks: connect to a server and list its tools.
  2. Real tool use: search YouTube and upload a file to Drive.

Nothing here claims success unless the server actually returned usable data.
Tool names and argument names differ between MCP servers, so they are read
from each tool's own schema instead of being hardcoded.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import re
from typing import Any, Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient

from models import LearningResource, LearningRoadmap

URL_PATTERN = re.compile(r"https?://[^\s\"'<>\)\]\}]+")

SEARCH_ARG_NAMES = ["query", "q", "search_query", "searchQuery", "term", "keyword", "keywords"]
FILENAME_ARG_NAMES = ["name", "file_name", "filename", "fileName", "title", "path"]
CONTENT_ARG_NAMES = ["content", "file_content", "fileContent", "text", "body", "data", "file_content_string"]


def _run_sync(coro):
    """Run a coroutine from sync code, even if this thread already has a loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def stringify(value: Any) -> str:
    """Flatten whatever a tool returned into plain text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, (list, tuple)):
        return "\n".join(stringify(item) for item in value)
    return str(value)


def extract_urls(text: str) -> List[str]:
    """Return unique URLs in order of appearance."""
    seen = set()
    urls: List[str] = []
    for raw in URL_PATTERN.findall(text or ""):
        url = raw.rstrip(".,;")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _schema_properties(tool: Any) -> Dict[str, Any]:
    """Parameter map for a tool, whether it exposes a flat map or a full schema."""
    args = getattr(tool, "args", None)
    if not isinstance(args, dict):
        return {}
    nested = args.get("properties")
    if isinstance(nested, dict) and nested and all(isinstance(value, dict) for value in nested.values()):
        return nested
    return args


def _pick_arg(properties: Dict[str, Any], candidates: List[str]) -> Optional[str]:
    lowered = {str(key).lower(): key for key in properties}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def looks_like_error(text: str) -> bool:
    """Conservative check: only flag text that clearly reports a failure."""
    if not text:
        return True
    lowered = text.lower()
    try:
        payload = json.loads(text)
    except (ValueError, TypeError):
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if error:
            return True
        if payload.get("success") is False:
            return True
    for marker in ("unauthorized", "forbidden", "permission denied", "invalid credentials"):
        if marker in lowered:
            return True
    return False


class MCPManager:
    """Connection, introspection and tool use for MCP servers."""

    @staticmethod
    def build_tools_config(
        youtube_url: Optional[str] = None,
        drive_url: Optional[str] = None,
        notion_url: Optional[str] = None,
    ) -> Dict[str, Dict[str, str]]:
        config: Dict[str, Dict[str, str]] = {}
        for name, url in (("youtube", youtube_url), ("drive", drive_url), ("notion", notion_url)):
            if url and url.strip():
                config[name] = {"url": url.strip(), "transport": "streamable_http"}
        return config

    # ------------------------------------------------------------------ health

    @classmethod
    async def test_server_connection(cls, name: str, url: str, timeout_seconds: float = 8.0) -> Dict[str, Any]:
        if not url or not url.strip():
            return {
                "server": name,
                "status": "unconfigured",
                "message": "No endpoint URL provided.",
                "tools": [],
                "descriptions": [],
            }
        config = {name: {"url": url.strip(), "transport": "streamable_http"}}
        try:
            tools = await asyncio.wait_for(cls.get_tools(config, timeout_seconds), timeout=timeout_seconds)
            names = [getattr(tool, "name", str(tool)) for tool in tools]
            return {
                "server": name,
                "status": "connected",
                "message": f"Connected. {len(names)} tool(s) available.",
                "tools": names,
                "descriptions": [getattr(tool, "description", "") for tool in tools],
            }
        except asyncio.TimeoutError:
            return {
                "server": name,
                "status": "timeout",
                "message": f"Timed out after {timeout_seconds:g}s. Check the URL and the Pipedream account permissions.",
                "tools": [],
                "descriptions": [],
            }
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI as text
            return {
                "server": name,
                "status": "error",
                "message": f"Connection failed: {exc}",
                "tools": [],
                "descriptions": [],
            }

    @classmethod
    def test_server_connection_sync(cls, name: str, url: str, timeout_seconds: float = 8.0) -> Dict[str, Any]:
        try:
            return _run_sync(cls.test_server_connection(name, url, timeout_seconds))
        except Exception as exc:  # noqa: BLE001
            return {
                "server": name,
                "status": "error",
                "message": f"Unexpected error during health check: {exc}",
                "tools": [],
                "descriptions": [],
            }

    # -------------------------------------------------------------------- tools

    @classmethod
    async def get_tools(cls, config: Dict[str, Dict[str, str]], timeout_seconds: float = 15.0):
        """Discover tools. Always bounded by a timeout."""
        if not config:
            return []
        client = MultiServerMCPClient(config)
        return await asyncio.wait_for(client.get_tools(), timeout=timeout_seconds)

    @staticmethod
    def pick_search_tool(tools: List[Any]) -> Optional[Any]:
        """Prefer an explicit search tool; ignore upload/download tools."""
        for tool in tools:
            name = getattr(tool, "name", "").lower()
            description = getattr(tool, "description", "").lower()
            if "search" in name or "search" in description:
                return tool
        return None

    @staticmethod
    def pick_upload_tool(tools: List[Any]) -> Optional[Any]:
        """Return the first tool that can accept both a name and a body."""
        for tool in tools:
            name = getattr(tool, "name", "").lower()
            if not any(word in name for word in ("create", "upload", "write", "save", "insert")):
                continue
            properties = _schema_properties(tool)
            if _pick_arg(properties, FILENAME_ARG_NAMES) and _pick_arg(properties, CONTENT_ARG_NAMES):
                return tool
        return None

    @classmethod
    async def _invoke_search(cls, tool: Any, query: str) -> List[str]:
        properties = _schema_properties(tool)
        query_arg = _pick_arg(properties, SEARCH_ARG_NAMES)
        if query_arg is None:
            string_args = [
                key for key, schema in properties.items()
                if isinstance(schema, dict) and schema.get("type") == "string"
            ]
            query_arg = string_args[0] if len(string_args) == 1 else None
        if query_arg is None:
            return []
        try:
            result = await tool.ainvoke({query_arg: query})
        except Exception:  # noqa: BLE001 - a failed search never breaks generation
            return []
        return extract_urls(stringify(result))

    @classmethod
    async def _search_many(cls, url: str, queries: List[str], timeout_seconds: float = 20.0) -> List[List[str]]:
        config = cls.build_tools_config(youtube_url=url)
        try:
            tools = await cls.get_tools(config, timeout_seconds)
        except Exception:  # noqa: BLE001
            return [[] for _ in queries]
        tool = cls.pick_search_tool(tools)
        if tool is None:
            return [[] for _ in queries]
        results: List[List[str]] = []
        for query in queries:
            results.append(await cls._invoke_search(tool, query))
        return results

    @classmethod
    def search_youtube_sync(cls, url: str, queries: List[str]) -> List[List[str]]:
        """Search several queries in one connection."""
        if not url or not queries:
            return [[] for _ in queries]
        try:
            return _run_sync(cls._search_many(url, queries))
        except Exception:  # noqa: BLE001
            return [[] for _ in queries]

    @classmethod
    def enrich_roadmap_with_youtube(
        cls,
        roadmap: LearningRoadmap,
        server_url: str,
        max_searches: int = 8,
        progress_callback: Optional[Any] = None,
    ) -> int:
        """
        Replace nothing, add nothing unless a real URL came back.

        Returns the number of days that gained a verified resource.
        """
        days = roadmap.days[:max_searches]
        if not days:
            return 0
        queries = [f"{day.topic_title} tutorial" for day in days]
        if progress_callback:
            progress_callback("Searching YouTube through MCP...", 0.88)
        results = cls.search_youtube_sync(server_url, queries)

        verified = 0
        for index, (day, urls) in enumerate(zip(days, results)):
            if not urls:
                continue
            url = next((candidate for candidate in urls if "youtube.com" in candidate or "youtu.be" in candidate), urls[0])
            if any(resource.url == url for resource in day.resources):
                continue
            day.resources.insert(
                0,
                LearningResource(
                    title=f"Live YouTube result: {day.topic_title}",
                    url=url,
                    platform="YouTube",
                    relevance_note="Returned by a live YouTube MCP search.",
                    is_mcp_verified=True,
                ),
            )
            day.resources = day.resources[:4]
            verified += 1
            if progress_callback:
                progress = 0.88 + (0.1 * (index + 1) / len(days))
                progress_callback(f"Verified resources for day {day.day_number}...", progress)
        return verified

    # ------------------------------------------------------------------- drive

    @classmethod
    async def _upload_text(
        cls,
        url: str,
        filename: str,
        content: str,
        timeout_seconds: float = 30.0,
    ) -> Dict[str, Any]:
        config = cls.build_tools_config(drive_url=url)
        try:
            tools = await cls.get_tools(config, timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "message": f"Could not reach the Google Drive MCP server: {exc}"}

        tool = cls.pick_upload_tool(tools)
        if tool is None:
            available = ", ".join(getattr(item, "name", "?") for item in tools) or "none"
            return {
                "success": False,
                "message": f"No file-creation tool found on the Drive server. Available tools: {available}",
            }

        properties = _schema_properties(tool)
        name_arg = _pick_arg(properties, FILENAME_ARG_NAMES)
        content_arg = _pick_arg(properties, CONTENT_ARG_NAMES)
        if not name_arg or not content_arg:
            return {"success": False, "message": "The Drive tool does not expose name/content arguments."}

        arguments = {name_arg: filename, content_arg: content}
        try:
            result = await tool.ainvoke(arguments)
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "message": f"Drive tool '{getattr(tool, 'name', '?')}' failed: {exc}"}

        text = stringify(result)
        if looks_like_error(text):
            return {"success": False, "message": f"Drive rejected the upload: {text[:300]}"}
        return {
            "success": True,
            "message": f"Saved '{filename}' through MCP tool '{getattr(tool, 'name', 'drive')}'.",
            "result": text[:500],
        }

    @classmethod
    def upload_text_sync(cls, url: str, filename: str, content: str) -> Dict[str, Any]:
        if not url or not url.strip():
            return {"success": False, "message": "Google Drive MCP URL is not configured."}
        try:
            return _run_sync(cls._upload_text(url.strip(), filename, content))
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "message": f"Unexpected Drive error: {exc}"}
