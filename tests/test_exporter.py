"""
Unit tests for RoadmapExporter (Markdown, JSON, and Google Drive).
"""

import json
import asyncio
import pytest
from models import LearningRoadmap, DayTopic, LearningResource, CapstoneProject
from exporter import RoadmapExporter


@pytest.fixture
def sample_roadmap():
    day1 = DayTopic(
        day_number=1,
        topic_title="Java Basics",
        estimated_time="2 Hours",
        concept_explanation="Introduction to variables and types.",
        key_takeaways=["Syntax", "Compilation"],
        resources=[
            LearningResource(
                title="Intro to Java",
                url="https://youtube.com/watch?v=sample",
                platform="YouTube",
                channel_or_author="TechGuru",
                is_mcp_verified=True
            )
        ],
        practice_exercises=["Exercise 1", "Exercise 2"],
        assignment="Write a greeting program",
        revision_checkpoint="What is javac?",
        completed=False
    )
    return LearningRoadmap(
        title="15-Day Java Mastery",
        goal="Master Java",
        skill_level="Beginner",
        total_duration="15 Days",
        daily_commitment="2 Hours/Day",
        expected_outcome="Build a full project",
        milestones=["Milestone 1"],
        days=[day1],
        capstone_project=CapstoneProject(
            title="Console Banking App",
            description="Manage user balances.",
            deliverables=["Account model", "Transaction log"]
        ),
        next_steps=["Learn Spring"]
    )


def test_export_markdown(sample_roadmap):
    """Verify Markdown export contains all critical sections."""
    md = RoadmapExporter.to_markdown(sample_roadmap)
    assert "# 15-Day Java Mastery" in md
    assert "Day 1: Java Basics" in md
    assert "Console Banking App" in md
    assert "[MCP Verified]" in md
    assert "What is javac?" in md


def test_export_json(sample_roadmap):
    """Verify JSON export produces valid JSON deserializable into dict."""
    json_str = RoadmapExporter.to_json(sample_roadmap)
    parsed = json.loads(json_str)
    assert parsed["title"] == "15-Day Java Mastery"
    assert len(parsed["days"]) == 1
    assert parsed["days"][0]["resources"][0]["is_mcp_verified"] is True


def test_save_to_google_drive_unconfigured(sample_roadmap):
    """Verify saving to Google Drive without URL yields graceful failure message."""
    res = asyncio.run(RoadmapExporter.save_to_google_drive_mcp(sample_roadmap, ""))
    assert res["success"] is False
    assert "not configured" in res["message"]
