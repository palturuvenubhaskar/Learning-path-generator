"""Tests for MCP discovery and tool use. All network calls are mocked."""

from __future__ import annotations

from unittest.mock import patch

from mcp_client import MCPManager, extract_urls, looks_like_error, stringify
from models import DayTopic, LearningRoadmap


class FakeTool:
    def __init__(self, name, properties=None, result=None, error=None):
        self.name = name
        self.description = f"{name} tool"
        self.args = properties or {}
        self.result = result
        self.error = error
        self.called_with = None

    async def ainvoke(self, arguments):
        self.called_with = arguments
        if self.error:
            raise self.error
        return self.result


class FakeClient:
    tools = []

    def __init__(self, config):
        self.config = config

    async def get_tools(self):
        return FakeClient.tools


def _search_tool(result):
    return FakeTool(
        "youtube_search",
        {"properties": {"query": {"type": "string"}}},
        result=result,
    )


def _upload_tool(result):
    return FakeTool(
        "create_file",
        {
            "properties": {
                "file_name": {"type": "string"},
                "file_content": {"type": "string"},
            }
        },
        result=result,
    )


def test_build_tools_config_empty():
    assert MCPManager.build_tools_config() == {}


def test_build_tools_config_maps_urls():
    config = MCPManager.build_tools_config(
        youtube_url="https://youtube.example/mcp",
        drive_url="https://drive.example/mcp",
        notion_url="https://notion.example/mcp",
    )
    assert config["youtube"]["transport"] == "streamable_http"
    assert config["drive"]["url"] == "https://drive.example/mcp"
    assert set(config) == {"youtube", "drive", "notion"}


def test_unconfigured_server_returns_early():
    result = MCPManager.test_server_connection_sync("youtube", "")
    assert result["status"] == "unconfigured"
    assert result["tools"] == []


def test_connected_server_lists_tools():
    FakeClient.tools = [_search_tool("[]")]
    with patch("mcp_client.MultiServerMCPClient", FakeClient):
        result = MCPManager.test_server_connection_sync("youtube", "https://example.invalid/mcp")
    assert result["status"] == "connected"
    assert result["tools"] == ["youtube_search"]


def test_search_tool_selection_skips_upload_tools():
    upload = _upload_tool("ok")
    search = _search_tool("ok")
    assert MCPManager.pick_search_tool([upload, search]) is search
    assert MCPManager.pick_search_tool([upload]) is None


def test_upload_tool_requires_name_and_content_arguments():
    good = _upload_tool("ok")
    bad = FakeTool("create_file", {"properties": {"title": {"type": "string"}}})
    assert MCPManager.pick_upload_tool([bad, good]) is good


def test_upload_sends_schema_argument_names():
    FakeClient.tools = [_upload_tool('{"id": "file-1", "webViewLink": "https://drive/x"}')]
    with patch("mcp_client.MultiServerMCPClient", FakeClient):
        result = MCPManager.upload_text_sync("https://drive.invalid/mcp", "plan.md", "# Plan")
    assert result["success"] is True
    tool = FakeClient.tools[0]
    assert tool.called_with == {"file_name": "plan.md", "file_content": "# Plan"}


def test_upload_reports_failure_from_tool_payload():
    FakeClient.tools = [_upload_tool('{"error": "insufficient permissions"}')]
    with patch("mcp_client.MultiServerMCPClient", FakeClient):
        result = MCPManager.upload_text_sync("https://drive.invalid/mcp", "plan.md", "# Plan")
    assert result["success"] is False
    assert "rejected" in result["message"].lower()


def test_upload_without_suitable_tool_fails():
    FakeClient.tools = [_search_tool("[]")]
    with patch("mcp_client.MultiServerMCPClient", FakeClient):
        result = MCPManager.upload_text_sync("https://drive.invalid/mcp", "plan.md", "# Plan")
    assert result["success"] is False
    assert "no file-creation tool" in result["message"].lower()


def test_upload_unconfigured_url():
    result = MCPManager.upload_text_sync("", "plan.md", "# Plan")
    assert result["success"] is False


def test_search_extracts_youtube_urls():
    FakeClient.tools = [
        _search_tool('{"items": [{"url": "https://www.youtube.com/watch?v=abc"}, '
                     '{"url": "https://example.com/not-video"}]}')
    ]
    with patch("mcp_client.MultiServerMCPClient", FakeClient):
        results = MCPManager.search_youtube_sync("https://yt.invalid/mcp", ["numpy tutorial"])
    assert results == [["https://www.youtube.com/watch?v=abc", "https://example.com/not-video"]]


def _roadmap(days=2):
    return LearningRoadmap(
        title="T",
        goal="G",
        total_duration=f"{days} Days",
        daily_commitment="1 Hour/Day",
        expected_outcome="O",
        days=[
            DayTopic(
                day_number=index + 1,
                topic_title=f"Topic {index + 1}",
                estimated_time="1 Hour",
                concept_explanation="x",
            )
            for index in range(days)
        ],
    )


def test_enrichment_only_marks_real_search_results():
    FakeClient.tools = [_search_tool("https://www.youtube.com/watch?v=real")]
    with patch("mcp_client.MultiServerMCPClient", FakeClient):
        verified = MCPManager.enrich_roadmap_with_youtube(_roadmap(2), "https://yt.invalid/mcp", max_searches=2)
    assert verified == 2


def test_enrichment_adds_nothing_when_search_is_empty():
    FakeClient.tools = [_search_tool("no results found")]
    roadmap = _roadmap(2)
    with patch("mcp_client.MultiServerMCPClient", FakeClient):
        verified = MCPManager.enrich_roadmap_with_youtube(roadmap, "https://yt.invalid/mcp", max_searches=2)
    assert verified == 0
    assert all(not day.resources for day in roadmap.days)


def test_extract_urls_is_unique_and_ordered():
    text = "a https://x.test/1 b https://x.test/1 c https://x.test/2."
    assert extract_urls(text) == ["https://x.test/1", "https://x.test/2"]


def test_stringify_handles_nested_values():
    assert "b" in stringify({"a": [{"b": 1}]})
    assert stringify(None) == ""


def test_looks_like_error():
    assert looks_like_error("") is True
    assert looks_like_error('{"error": "bad"}') is True
    assert looks_like_error('{"error": null, "id": "1"}') is False
    assert looks_like_error("Unauthorized") is True
    assert looks_like_error("file created") is False
