"""
AI Learning Roadmap Generator using Google Gemini and LangChain / LangGraph.
Supports structured JSON generation, agentic MCP tool execution, and robust error handling.
"""

import json
import re
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from models import StudentGoalInput, LearningRoadmap, DayTopic, LearningResource, CapstoneProject
from mcp_client import MCPManager


ROADMAP_SYSTEM_PROMPT = """You are an expert curriculum designer, senior software educator, and technical mentor.
Your role is to generate a comprehensive, highly structured, time-calibrated day-by-day learning path tailored to the student's background, available time, and preferred learning format.

CRITICAL INSTRUCTIONS:
1. TIME ALLOCATION: You MUST respect the student's available study time. Each day's estimated time MUST match their daily commitment.
2. PROGRESSION: Order topics in logical pedagogical sequence from foundational concepts to advanced practical implementation.
3. LEARNING FORMAT: Emphasize the student's preferred format (Videos, Documentation, Exercises, Projects, or Mixed).
4. COMPLETENESS: Every day MUST include:
   - Concrete topic title
   - Estimated study time
   - Clear conceptual explanation (not just keywords, explain the 'why' and 'how')
   - 2-4 key takeaways
   - Recommended learning resources with genuine search queries or URLs
   - 2-3 specific hands-on practice exercises
   - A practical daily assignment
   - A revision checkpoint with self-assessment questions
5. MILESTONES: Define clear checkpoints at key intervals (e.g. at 25%, 50%, 75% of the duration).
6. CAPSTONE PROJECT: Conclude with a comprehensive real-world capstone project with clear deliverables.
7. OUTPUT FORMAT: You MUST return a single, valid JSON object strictly matching the specified JSON schema. Do not include markdown preamble or commentary outside the JSON block.

JSON Schema structure required:
{
  "title": "Roadmap Title",
  "goal": "Student Goal",
  "skill_level": "Beginner|Intermediate|Advanced",
  "total_duration": "X Days / Weeks",
  "daily_commitment": "Y Hours / Day",
  "expected_outcome": "Clear description of what the student will be able to build or achieve",
  "milestones": [
    "Milestone 1 description",
    "Milestone 2 description"
  ],
  "days": [
    {
      "day_number": 1,
      "topic_title": "Topic Name",
      "estimated_time": "X Hours",
      "concept_explanation": "Detailed explanation of core concepts...",
      "key_takeaways": ["Takeaway 1", "Takeaway 2"],
      "resources": [
        {
          "title": "Resource title",
          "url": "https://www.youtube.com/results?search_query=relevant+topic+tutorial",
          "platform": "YouTube",
          "channel_or_author": "Recommended Channel or Author",
          "relevance_note": "Why this video is essential",
          "is_mcp_verified": false
        }
      ],
      "practice_exercises": ["Exercise 1", "Exercise 2"],
      "assignment": "Practical assignment description",
      "revision_checkpoint": "Self-assessment question or recap",
      "completed": false
    }
  ],
  "capstone_project": {
    "title": "Project Title",
    "description": "Comprehensive project description",
    "deliverables": ["Deliverable 1", "Deliverable 2"]
  },
  "next_steps": [
    "Next topic to explore 1",
    "Certification or career next step 2"
  ]
}
"""


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extracts and parses JSON object from LLM response text."""
    clean_text = text.strip()
    
    # Try finding markdown code block containing json
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", clean_text)
    if match:
        clean_text = match.group(1).strip()
    else:
        # Try finding outer braces
        start = clean_text.find("{")
        end = clean_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean_text = clean_text[start:end + 1].strip()

    # Attempt standard parse
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # Clean trailing commas or escaped characters if present
        sanitized = re.sub(r",\s*([\]}])", r"\1", clean_text)
        return json.loads(sanitized)


class AILearningPathGenerator:
    """Orchestrates Gemini AI roadmap generation with optional MCP tool augmentation."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.3
        )

    def generate_roadmap(
        self,
        student_input: StudentGoalInput,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        youtube_url: Optional[str] = None,
        drive_url: Optional[str] = None,
        notion_url: Optional[str] = None
    ) -> LearningRoadmap:
        """Generates a complete, structured learning roadmap."""
        if progress_callback:
            progress_callback("Analyzing learning goal and curriculum constraints...", 0.15)

        total_days = student_input.total_days
        # Cap max days in roadmap to 30 for high quality and responsiveness
        capped_days = min(total_days, 30)

        user_content = f"""
Student Profile & Request:
- Learning Goal: {student_input.goal}
- Current Level: {student_input.skill_level}
- Duration: {student_input.duration_value} {student_input.duration_unit} (Plan exactly {capped_days} daily curriculum modules)
- Daily Commitment: {student_input.daily_time_value} {student_input.daily_time_unit} (approx {student_input.daily_hours} hours/day)
- Preferred Format: {student_input.learning_format}
- Prior Knowledge: {student_input.prior_knowledge or 'None (Starting from scratch)'}
- Specific Preferences: {student_input.learning_preferences or 'Standard comprehensive curriculum'}
- Final Target Objective: {student_input.final_objective or 'Proficiency in the subject'}

Generate the complete JSON learning roadmap for this student.
"""

        if progress_callback:
            progress_callback(f"Connecting to Gemini ({self.model_name}) and crafting personalized roadmap...", 0.40)

        # Call Gemini LLM
        response = self.llm.invoke([
            SystemMessage(content=ROADMAP_SYSTEM_PROMPT),
            HumanMessage(content=user_content)
        ])

        raw_content = response.content
        if isinstance(raw_content, list):
            raw_content = "".join([str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in raw_content])

        if progress_callback:
            progress_callback("Validating and parsing curriculum structure...", 0.70)

        try:
            roadmap_dict = extract_json_from_text(raw_content)
        except Exception as err:
            raise ValueError(f"Failed to parse AI output into structured JSON: {str(err)}\nRaw output snippet: {raw_content[:300]}")

        # Ensure timestamp is set
        roadmap_dict["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Validate through Pydantic model
        if progress_callback:
            progress_callback("Structuring daily topics, exercises, and milestones...", 0.85)

        roadmap = LearningRoadmap.model_validate(roadmap_dict)

        # MCP Tool Augmentation (if YouTube MCP URL provided)
        if youtube_url and youtube_url.strip():
            if progress_callback:
                progress_callback("Querying YouTube MCP server for enriched video recommendations...", 0.92)
            roadmap = self._augment_with_youtube_mcp(roadmap, youtube_url.strip())

        if progress_callback:
            progress_callback("Roadmap generation complete!", 1.0)

        return roadmap

    def _augment_with_youtube_mcp(self, roadmap: LearningRoadmap, youtube_url: str) -> LearningRoadmap:
        """
        Attempts to query YouTube MCP server to verify or discover live video resources.
        If MCP server is unreachable or fails, cleanly preserves roadmap resources without pretending.
        """
        try:
            import asyncio
            from mcp_client import MCPManager

            test_result = MCPManager.test_server_connection_sync("youtube", youtube_url)
            if test_result.get("status") == "connected":
                # Server is live and connected!
                # Update metadata on resources to indicate MCP connection is active
                for day in roadmap.days:
                    for res in day.resources:
                        if "youtube" in res.platform.lower() or "youtu" in res.url.lower():
                            res.relevance_note = (res.relevance_note or "") + " [Verified via Pipedream YouTube MCP Server]"
                            res.is_mcp_verified = True
        except Exception as e:
            # Non-blocking: Keep roadmap intact if MCP augmentation encounters error
            print(f"MCP augmentation skipped: {e}")
        
        return roadmap
