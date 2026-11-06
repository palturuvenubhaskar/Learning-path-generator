"""Export a roadmap as Markdown, JSON, or a file saved through the Drive MCP server."""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from models import LearningRoadmap

_ILLEGAL_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_filename(text: str, extension: str, fallback: str = "learning-roadmap") -> str:
    """Turn a model-generated title into a filename Windows accepts."""
    cleaned = _ILLEGAL_FILENAME.sub("", text or "").strip().strip(".")
    cleaned = re.sub(r"\s+", "_", cleaned)[:80].strip("_")
    return f"{cleaned or fallback}.{extension}"


class RoadmapExporter:
    """Formats and stores a plan."""

    @staticmethod
    def to_markdown(roadmap: LearningRoadmap) -> str:
        lines = [f"# {roadmap.title}", ""]
        lines.append(f"**Goal:** {roadmap.goal}  ")
        lines.append(f"**Level:** {roadmap.skill_level}  ")
        lines.append(f"**Duration:** {roadmap.total_duration}  ")
        lines.append(f"**Daily commitment:** {roadmap.daily_commitment}  ")
        if roadmap.requested_days and roadmap.requested_days != len(roadmap.days):
            lines.append(
                f"**Note:** you asked for {roadmap.requested_days} days; this plan has "
                f"{len(roadmap.days)}.  "
            )
        if roadmap.created_at:
            lines.append(f"**Created:** {roadmap.created_at}  ")
        lines.append("")
        lines.append("## Expected outcome")
        lines.append(roadmap.expected_outcome)
        lines.append("")

        if roadmap.milestones:
            lines.append("## Milestones")
            for index, milestone in enumerate(roadmap.milestones, 1):
                lines.append(f"{index}. {milestone}")
            lines.append("")

        lines.append("## Day-by-day plan")
        lines.append("")
        for day in roadmap.days:
            done = " [done]" if day.completed else ""
            lines.append(f"### Day {day.day_number}: {day.topic_title}{done}")
            lines.append(f"- **Time:** {day.estimated_time}")
            lines.append("")
            lines.append(day.concept_explanation)
            lines.append("")

            if day.key_takeaways:
                lines.append("**Key takeaways**")
                for item in day.key_takeaways:
                    lines.append(f"- {item}")
                lines.append("")

            if day.resources:
                lines.append("**Resources**")
                for resource in day.resources:
                    tag = " `[MCP verified]`" if resource.is_mcp_verified else ""
                    author = f" — {resource.channel_or_author}" if resource.channel_or_author else ""
                    lines.append(f"- [{resource.title}]({resource.url}) ({resource.platform}){author}{tag}")
                lines.append("")

            if day.practice_exercises:
                lines.append("**Practice**")
                for exercise in day.practice_exercises:
                    lines.append(f"- [ ] {exercise}")
                lines.append("")

            if day.assignment:
                lines.append(f"> **Assignment:** {day.assignment}")
                lines.append("")

            if day.revision_checkpoint:
                lines.append(f"> **Revision:** {day.revision_checkpoint}")
                lines.append("")

            lines.append("---")
            lines.append("")

        if roadmap.capstone_project:
            lines.append("## Capstone project")
            lines.append(f"### {roadmap.capstone_project.title}")
            lines.append(roadmap.capstone_project.description)
            lines.append("")
            for deliverable in roadmap.capstone_project.deliverables:
                lines.append(f"- {deliverable}")
            lines.append("")

        if roadmap.next_steps:
            lines.append("## Next steps")
            for step in roadmap.next_steps:
                lines.append(f"- {step}")
            lines.append("")

        lines.append("---")
        lines.append("*Generated with the Learning Path Generator.*")
        return "\n".join(lines)

    @staticmethod
    def to_json(roadmap: LearningRoadmap) -> str:
        return roadmap.model_dump_json(indent=2)

    @staticmethod
    def to_dict(roadmap: LearningRoadmap) -> Dict[str, Any]:
        return json.loads(roadmap.model_dump_json())

    @classmethod
    def save_to_google_drive_mcp(cls, roadmap: LearningRoadmap, drive_mcp_url: str) -> Dict[str, Any]:
        if not drive_mcp_url or not drive_mcp_url.strip():
            return {"success": False, "message": "Google Drive MCP URL is not configured."}
        from mcp_client import MCPManager

        filename = safe_filename(roadmap.title, "md")
        return MCPManager.upload_text_sync(drive_mcp_url, filename, cls.to_markdown(roadmap))
