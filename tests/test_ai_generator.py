"""
Unit tests for AI Generator, JSON extraction, and roadmap synthesis.
"""

import pytest
from unittest.mock import MagicMock, patch
from ai_generator import extract_json_from_text, AILearningPathGenerator
from models import StudentGoalInput, LearningRoadmap


def test_extract_json_from_markdown():
    """Verify parsing JSON wrapped in markdown code fence."""
    raw = """
Here is the learning roadmap you requested:
```json
{
  "title": "Python Bootcamp",
  "goal": "Learn Python",
  "skill_level": "Beginner",
  "total_duration": "5 Days",
  "daily_commitment": "1 Hour/Day",
  "expected_outcome": "Write scripts",
  "milestones": ["Day 3 milestone"],
  "days": []
}
```
Hope this helps!
"""
    parsed = extract_json_from_text(raw)
    assert parsed["title"] == "Python Bootcamp"
    assert parsed["goal"] == "Learn Python"


def test_extract_json_plain():
    """Verify parsing plain JSON string."""
    raw = '{"title": "Java Path", "goal": "Java", "skill_level": "Beginner", "total_duration": "10 Days", "daily_commitment": "2 Hours/Day", "expected_outcome": "Build apps", "days": []}'
    parsed = extract_json_from_text(raw)
    assert parsed["title"] == "Java Path"


def test_ai_generator_pipeline_mocked():
    """Verify AILearningPathGenerator correctly parses LLM response into LearningRoadmap."""
    mock_response_json = """
    ```json
    {
      "title": "15-Day Java Mastery",
      "goal": "Learn Java programming in 15 days",
      "skill_level": "Beginner",
      "total_duration": "15 Days",
      "daily_commitment": "2 Hours/Day",
      "expected_outcome": "Build object-oriented applications",
      "milestones": ["Understand OOP by Day 7", "Build CLI project by Day 15"],
      "days": [
        {
          "day_number": 1,
          "topic_title": "Java Environment & Syntax",
          "estimated_time": "2 Hours",
          "concept_explanation": "Install JDK, understand JVM and bytecode.",
          "key_takeaways": ["JVM vs JRE vs JDK", "Basic data types"],
          "resources": [
            {
              "title": "Java in 100 Seconds",
              "url": "https://www.youtube.com/watch?v=l9AzO1FMgM8",
              "platform": "YouTube",
              "channel_or_author": "Fireship",
              "relevance_note": "High-level overview",
              "is_mcp_verified": false
            }
          ],
          "practice_exercises": ["Install JDK", "Write HelloWorld"],
          "assignment": "Write a temperature converter",
          "revision_checkpoint": "What is the role of the JVM?",
          "completed": false
        }
      ],
      "capstone_project": {
        "title": "Student Management System",
        "description": "A console-based CRUD application.",
        "deliverables": ["Source code", "Documentation"]
      },
      "next_steps": ["Learn Spring Boot", "Study Data Structures"]
    }
    ```
    """

    generator = AILearningPathGenerator(api_key="mock_key", model_name="gemini-2.5-flash")
    
    mock_msg = MagicMock()
    mock_msg.content = mock_response_json
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_msg
    generator.llm = mock_llm

    student_input = StudentGoalInput(
        goal="Learn Java in 15 days",
        skill_level="Beginner",
        duration_value=15,
        duration_unit="Days",
        daily_time_value=2.0,
        daily_time_unit="Hours"
    )
    roadmap = generator.generate_roadmap(student_input)
    
    assert isinstance(roadmap, LearningRoadmap)
    assert roadmap.title == "15-Day Java Mastery"
    assert len(roadmap.days) == 1
    assert roadmap.days[0].topic_title == "Java Environment & Syntax"
    assert roadmap.capstone_project.title == "Student Management System"
