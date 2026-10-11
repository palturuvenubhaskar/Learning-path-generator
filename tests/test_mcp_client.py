"""
Unit tests for MCP Client and connection manager.
"""

import pytest
from mcp_client import MCPManager


def test_build_tools_config_empty():
    """Verify empty config returned when no URLs are supplied."""
    cfg = MCPManager.build_tools_config()
    assert cfg == {}


def test_build_tools_config_with_urls():
    """Verify tools config properly maps YouTube, Drive, and Notion streamable_http endpoints."""
    cfg = MCPManager.build_tools_config(
        youtube_url="https://youtube.mcp.example.com",
        drive_url="https://drive.mcp.example.com",
        notion_url="https://notion.mcp.example.com"
    )
    assert "youtube" in cfg
    assert cfg["youtube"]["url"] == "https://youtube.mcp.example.com"
    assert cfg["youtube"]["transport"] == "streamable_http"
    assert "drive" in cfg
    assert "notion" in cfg


def test_test_server_connection_unconfigured():
    """Verify unconfigured server returns unconfigured status."""
    res = MCPManager.test_server_connection_sync("youtube", "")
    assert res["status"] == "unconfigured"
    assert res["tools"] == []


def test_test_server_connection_invalid_url():
    """Verify invalid URL fails gracefully without uncaught exception."""
    res = MCPManager.test_server_connection_sync("youtube", "http://localhost:9999/invalid")
    assert res["status"] in ["error", "timeout"]
    assert res["tools"] == []
