"""Tests for Markdown/JSON export and the Drive wrapper."""

import json
from unittest.mock import patch

import pytest

from exporter import RoadmapExporter, safe_filename
from models import CapstoneProject, DayTopic, LearningResource, LearningRoadmap


@pytest.fixture
def sample_roadmap():
    day = DayTopic(
        day_number=1,
        topic_title="Java Basics",
        estimated_time="2 Hours",
        concept_explanation="Variables and types.",
        key_takeaways=["Syntax"],
        resources=[
            LearningResource(
                title="Intro to Java",
                url="https://youtube.com/watch?v=sample",
                platform="YouTube",
                channel_or_author="TechGuru",
                is_mcp_verified=True,
            )
        ],
        practice_exercises=["Exercise 1"],
        assignment="Write a greeting program",
        revision_checkpoint="What is javac?",
    )
    return LearningRoadmap(
        title="15-Day Java Mastery",
        goal="Master Java",
        skill_level="Beginner",
        total_duration="15 Days",
        daily_commitment="2 Hours/Day",
        expected_outcome="Build a project",
        milestones=["Milestone 1"],
        days=[day],
        capstone_project=CapstoneProject(
            title="Console Banking App",
            description="Manage balances.",
            deliverables=["Account model"],
        ),
        next_steps=["Learn Spring"],
        requested_days=15,
    )


def test_markdown_contains_key_sections(sample_roadmap):
    markdown = RoadmapExporter.to_markdown(sample_roadmap)
    assert "# 15-Day Java Mastery" in markdown
    assert "Day 1: Java Basics" in markdown
    assert "Console Banking App" in markdown
    assert "[MCP verified]" in markdown
    assert "What is javac?" in markdown


def test_markdown_is_honest_about_day_count(sample_roadmap):
    markdown = RoadmapExporter.to_markdown(sample_roadmap)
    assert "you asked for 15 days" in markdown


def test_json_roundtrip(sample_roadmap):
    parsed = json.loads(RoadmapExporter.to_json(sample_roadmap))
    assert parsed["title"] == "15-Day Java Mastery"
    assert parsed["days"][0]["resources"][0]["is_mcp_verified"] is True


def test_drive_unconfigured_does_not_call_network(sample_roadmap):
    with patch("mcp_client.MCPManager.upload_text_sync") as upload:
        result = RoadmapExporter.save_to_google_drive_mcp(sample_roadmap, "")
    assert result["success"] is False
    upload.assert_not_called()


def test_drive_uses_safe_filename(sample_roadmap):
    with patch("mcp_client.MCPManager.upload_text_sync", return_value={"success": True}) as upload:
        RoadmapExporter.save_to_google_drive_mcp(sample_roadmap, "https://drive.invalid/mcp")
    _, filename, content = upload.call_args[0]
    assert filename == "15-Day_Java_Mastery.md"
    assert content.startswith("# 15-Day Java Mastery")


def test_safe_filename_removes_windows_illegal_characters():
    assert safe_filename('Q3: "results"/final', "md") == "Q3_resultsfinal.md"
