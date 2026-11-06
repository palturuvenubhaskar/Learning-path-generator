"""
Pydantic models: validated student input and the generated roadmap.

These are the single source of truth for input rules and progress math.
The UI reads the computed properties instead of redoing the arithmetic.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ALLOWED_SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced"]
ALLOWED_FORMATS = ["Mixed", "Videos", "Documentation", "Exercises", "Projects"]
ALLOWED_DURATION_UNITS = ["Days", "Weeks"]
ALLOWED_TIME_UNITS = ["Hours", "Minutes"]

MAX_DAILY_HOURS = 16.0
MAX_DAILY_MINUTES = 960.0


class StudentGoalInput(BaseModel):
    """Validated user input for one roadmap request."""

    goal: str = Field(..., min_length=3, max_length=400, description="Subject or goal to learn")
    skill_level: str = Field("Beginner", description="Beginner, Intermediate or Advanced")
    duration_value: int = Field(14, ge=1, le=180, description="Numeric duration value")
    duration_unit: str = Field("Days", description="Days or Weeks")
    daily_time_value: float = Field(2.0, gt=0, le=MAX_DAILY_MINUTES, description="Daily study time")
    daily_time_unit: str = Field("Hours", description="Hours or Minutes")
    learning_format: str = Field("Mixed", description="Preferred learning format")
    prior_knowledge: Optional[str] = Field(None, max_length=1000)
    learning_preferences: Optional[str] = Field(None, max_length=1000)
    final_objective: Optional[str] = Field(None, max_length=500)

    @field_validator("goal")
    @classmethod
    def _strip_goal(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Goal must be at least 3 characters")
        return cleaned

    @field_validator("skill_level")
    @classmethod
    def _check_skill(cls, value: str) -> str:
        if value not in ALLOWED_SKILL_LEVELS:
            raise ValueError(f"Skill level must be one of {ALLOWED_SKILL_LEVELS}")
        return value

    @field_validator("duration_unit")
    @classmethod
    def _check_duration_unit(cls, value: str) -> str:
        if value not in ALLOWED_DURATION_UNITS:
            raise ValueError(f"Duration unit must be one of {ALLOWED_DURATION_UNITS}")
        return value

    @field_validator("daily_time_unit")
    @classmethod
    def _check_time_unit(cls, value: str) -> str:
        if value not in ALLOWED_TIME_UNITS:
            raise ValueError(f"Daily time unit must be one of {ALLOWED_TIME_UNITS}")
        return value

    @field_validator("learning_format")
    @classmethod
    def _check_format(cls, value: str) -> str:
        if value not in ALLOWED_FORMATS:
            raise ValueError(f"Learning format must be one of {ALLOWED_FORMATS}")
        return value

    @model_validator(mode="after")
    def _check_daily_time_for_unit(self) -> "StudentGoalInput":
        """A limit only makes sense per unit: 16 hours or 960 minutes."""
        if self.daily_time_unit == "Hours" and self.daily_time_value > MAX_DAILY_HOURS:
            raise ValueError(f"Daily study time cannot exceed {MAX_DAILY_HOURS:g} hours")
        if self.daily_time_unit == "Minutes" and self.daily_time_value > MAX_DAILY_MINUTES:
            raise ValueError(f"Daily study time cannot exceed {MAX_DAILY_MINUTES:g} minutes")
        return self

    @property
    def total_days(self) -> int:
        return self.duration_value * 7 if self.duration_unit == "Weeks" else self.duration_value

    @property
    def daily_hours(self) -> float:
        if self.daily_time_unit == "Minutes":
            return round(self.daily_time_value / 60.0, 2)
        return round(self.daily_time_value, 2)

    @property
    def total_estimated_hours(self) -> float:
        return round(self.total_days * self.daily_hours, 1)


class LearningResource(BaseModel):
    """One link attached to a learning day."""

    title: str = Field(..., description="Title of the tutorial, video or documentation")
    url: str = Field(..., description="Web link")
    platform: str = Field("Web", description="YouTube, Official Docs, GitHub, ...")
    channel_or_author: Optional[str] = None
    relevance_note: Optional[str] = None
    is_mcp_verified: bool = Field(
        False,
        description="True only when a live MCP search returned this exact URL",
    )


class DayTopic(BaseModel):
    """One day of the plan."""

    day_number: int = Field(..., ge=1)
    topic_title: str
    estimated_time: str
    concept_explanation: str
    key_takeaways: List[str] = Field(default_factory=list)
    resources: List[LearningResource] = Field(default_factory=list)
    practice_exercises: List[str] = Field(default_factory=list)
    assignment: Optional[str] = None
    revision_checkpoint: Optional[str] = None
    completed: bool = False


class CapstoneProject(BaseModel):
    title: str
    description: str
    deliverables: List[str] = Field(default_factory=list)


class LearningRoadmap(BaseModel):
    """A complete plan, persisted and exported as-is."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    goal: str
    skill_level: str = "Beginner"
    total_duration: str
    daily_commitment: str
    expected_outcome: str
    milestones: List[str] = Field(default_factory=list)
    days: List[DayTopic] = Field(default_factory=list)
    capstone_project: Optional[CapstoneProject] = None
    next_steps: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None

    # How many days the student actually asked for. Lets the UI be honest when
    # the request was capped or the model returned a different number of days.
    requested_days: Optional[int] = None

    @model_validator(mode="after")
    def _normalize_day_numbers(self) -> "LearningRoadmap":
        """Keep day numbers unique and sequential so UI keys can't collide."""
        if not self.days:
            return self
        ordered = sorted(self.days, key=lambda day: day.day_number)
        numbers = [day.day_number for day in ordered]
        if len(set(numbers)) != len(numbers) or numbers != list(range(1, len(numbers) + 1)):
            for index, day in enumerate(ordered, start=1):
                day.day_number = index
            self.days = ordered
        return self

    @property
    def total_days_count(self) -> int:
        return len(self.days)

    def apply_completion(self, completion: dict[int, bool]) -> "LearningRoadmap":
        """Copy checkbox state onto the day objects, so exports are correct."""
        for day in self.days:
            day.completed = bool(completion.get(day.day_number, False))
        return self

    @property
    def completed_count(self) -> int:
        return sum(1 for day in self.days if day.completed)

    @property
    def progress_percentage(self) -> float:
        if not self.days:
            return 0.0
        return round((self.completed_count / len(self.days)) * 100.0, 1)

    @property
    def day_count_matches_request(self) -> bool:
        if self.requested_days is None:
            return True
        return self.requested_days == len(self.days)
