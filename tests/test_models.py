"""
Unit tests for data models and input validation.
"""

import pytest
from pydantic import ValidationError
from models import StudentGoalInput, LearningResource, DayTopic, LearningRoadmap, CapstoneProject


def test_student_goal_input_valid():
    """Verify valid student input instantiates correctly and calculates normalized metrics."""
    data = StudentGoalInput(
        goal="Learn Java in 15 days",
        skill_level="Beginner",
        duration_value=15,
        duration_unit="Days",
        daily_time_value=2.0,
        daily_time_unit="Hours",
        learning_format="Mixed"
    )
    assert data.total_days == 15
    assert data.daily_hours == 2.0
    assert data.total_estimated_hours == 30.0


def test_student_goal_input_weeks_and_minutes():
    """Verify conversion for weeks and minutes."""
    data = StudentGoalInput(
        goal="Full Stack Development",
        skill_level="Intermediate",
        duration_value=2,
        duration_unit="Weeks",
        daily_time_value=90.0,
        daily_time_unit="Minutes",
        learning_format="Projects"
    )
    assert data.total_days == 14
    assert data.daily_hours == 1.5
    assert data.total_estimated_hours == 21.0


def test_student_goal_input_invalid_skill_level():
    """Verify invalid skill level raises ValidationError."""
    with pytest.raises(ValidationError):
        StudentGoalInput(
            goal="Python",
            skill_level="Master",  # Invalid
            duration_value=10,
            duration_unit="Days",
            daily_time_value=1.0,
            daily_time_unit="Hours"
        )


def test_student_goal_input_invalid_duration():
    """Verify out-of-range duration raises ValidationError."""
    with pytest.raises(ValidationError):
        StudentGoalInput(
            goal="Python",
            duration_value=0,  # Invalid: ge=1
            duration_unit="Days",
            daily_time_value=1.0,
            daily_time_unit="Hours"
        )


def test_learning_roadmap_progress_tracking():
    """Verify progress tracking calculation when topics are completed."""
    day1 = DayTopic(
        day_number=1,
        topic_title="Java Syntax Basics",
        estimated_time="2 Hours",
        concept_explanation="Understanding variables, primitives, and syntax.",
        key_takeaways=["Variables", "Data types"],
        practice_exercises=["Write Hello World", "Declare variables"],
        completed=True
    )
    day2 = DayTopic(
        day_number=2,
        topic_title="Control Flow",
        estimated_time="2 Hours",
        concept_explanation="If-else and loops.",
        practice_exercises=["Implement fizzbuzz"],
        completed=False
    )
    roadmap = LearningRoadmap(
        title="15-Day Java Mastery",
        goal="Master Java",
        skill_level="Beginner",
        total_duration="15 Days",
        daily_commitment="2 Hours/Day",
        expected_outcome="Build a Java CLI app",
        days=[day1, day2]
    )

    assert roadmap.total_days_count == 2
    assert roadmap.completed_count == 1
    assert roadmap.progress_percentage == 50.0

    # Mark day 2 complete
    roadmap.days[1].completed = True
    assert roadmap.completed_count == 2
    assert roadmap.progress_percentage == 100.0
