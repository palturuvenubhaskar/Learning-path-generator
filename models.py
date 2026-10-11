"""
Pydantic data models for the AI Learning Path Generator.
Handles validation of student inputs and strict structuring of generated learning roadmaps.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class StudentGoalInput(BaseModel):
    """Validated user inputs for generating a personalized learning path."""
    goal: str = Field(..., min_length=3, description="Subject or goal the student wants to learn")
    skill_level: str = Field("Beginner", description="Current skill level: Beginner, Intermediate, or Advanced")
    duration_value: int = Field(14, ge=1, le=180, description="Available study duration numeric value")
    duration_unit: str = Field("Days", description="Duration unit: Days or Weeks")
    daily_time_value: float = Field(2.0, gt=0, le=960.0, description="Daily study time numeric value")
    daily_time_unit: str = Field("Hours", description="Daily time unit: Hours or Minutes")
    learning_format: str = Field("Mixed", description="Preferred format: Videos, Documentation, Exercises, Projects, Mixed")
    prior_knowledge: Optional[str] = Field(None, description="Topics already understood")
    learning_preferences: Optional[str] = Field(None, description="Specific learning style or constraints")
    final_objective: Optional[str] = Field(None, description="Exam prep, portfolio project, interview, etc.")

    @field_validator("daily_time_value")
    @classmethod
    def validate_daily_time(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Daily study time must be greater than 0")
        return v

    @field_validator("skill_level")
    @classmethod
    def validate_skill_level(cls, v: str) -> str:
        allowed = ["Beginner", "Intermediate", "Advanced"]
        if v not in allowed:
            raise ValueError(f"Skill level must be one of {allowed}")
        return v

    @field_validator("duration_unit")
    @classmethod
    def validate_duration_unit(cls, v: str) -> str:
        if v not in ["Days", "Weeks"]:
            raise ValueError("Duration unit must be either 'Days' or 'Weeks'")
        return v

    @field_validator("daily_time_unit")
    @classmethod
    def validate_daily_time_unit(cls, v: str) -> str:
        if v not in ["Hours", "Minutes"]:
            raise ValueError("Daily time unit must be either 'Hours' or 'Minutes'")
        return v

    @property
    def total_days(self) -> int:
        """Normalized duration in days."""
        return self.duration_value * 7 if self.duration_unit == "Weeks" else self.duration_value

    @property
    def daily_hours(self) -> float:
        """Normalized daily study time in hours."""
        return round(self.daily_time_value / 60.0, 2) if self.daily_time_unit == "Minutes" else self.daily_time_value

    @property
    def total_estimated_hours(self) -> float:
        """Total study commitment in hours."""
        return round(self.total_days * self.daily_hours, 1)


class LearningResource(BaseModel):
    """Resource attached to a learning day/topic."""
    title: str = Field(..., description="Title of the tutorial, video, or documentation")
    url: str = Field(..., description="Web link or YouTube video URL")
    platform: str = Field("YouTube", description="YouTube, Official Docs, GitHub, etc.")
    channel_or_author: Optional[str] = Field(None, description="Channel name or author")
    relevance_note: Optional[str] = Field(None, description="Why this resource is essential for the topic")
    is_mcp_verified: bool = Field(False, description="Whether this resource was retrieved via live MCP tool call")


class DayTopic(BaseModel):
    """Single day or session module in the learning path."""
    day_number: int = Field(..., ge=1, description="Day index (e.g. Day 1, Day 2)")
    topic_title: str = Field(..., description="Core topic or module name")
    estimated_time: str = Field(..., description="Estimated study duration, e.g. '2 hours'")
    concept_explanation: str = Field(..., description="Clear explanation of core concepts")
    key_takeaways: List[str] = Field(default_factory=list, description="Key points to remember")
    resources: List[LearningResource] = Field(default_factory=list, description="Curated resources for this day")
    practice_exercises: List[str] = Field(default_factory=list, description="Hands-on coding or concept exercises")
    assignment: Optional[str] = Field(None, description="Small practical assignment for the day")
    revision_checkpoint: Optional[str] = Field(None, description="Self-check questions or recap")
    completed: bool = Field(False, description="Completion status tracked in student session")


class CapstoneProject(BaseModel):
    """Final assessment or practical project completing the learning path."""
    title: str = Field(..., description="Project name")
    description: str = Field(..., description="Overview of the real-world project to build")
    deliverables: List[str] = Field(default_factory=list, description="Key deliverables or evaluation criteria")


class LearningRoadmap(BaseModel):
    """Complete personalized learning roadmap."""
    title: str = Field(..., description="Roadmap title")
    goal: str = Field(..., description="Target learning goal")
    skill_level: str = Field("Beginner", description="Target student skill level")
    total_duration: str = Field(..., description="Total duration summary, e.g. '15 Days'")
    daily_commitment: str = Field(..., description="Daily time commitment, e.g. '2 Hours/Day'")
    expected_outcome: str = Field(..., description="What the student will achieve by the end")
    milestones: List[str] = Field(default_factory=list, description="Major milestones along the way")
    days: List[DayTopic] = Field(default_factory=list, description="List of day-by-day learning units")
    capstone_project: Optional[CapstoneProject] = Field(None, description="Final practical capstone project")
    next_steps: List[str] = Field(default_factory=list, description="Suggestions for what to learn next")
    created_at: Optional[str] = Field(None, description="Timestamp of generation")

    @property
    def total_days_count(self) -> int:
        return len(self.days)

    @property
    def completed_count(self) -> int:
        return sum(1 for d in self.days if d.completed)

    @property
    def progress_percentage(self) -> float:
        if not self.days:
            return 0.0
        return round((self.completed_count / len(self.days)) * 100.0, 1)
