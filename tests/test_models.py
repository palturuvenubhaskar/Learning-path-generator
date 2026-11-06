"""Tests for input validation, day normalisation and progress maths."""

import pytest
from pydantic import ValidationError

from models import DayTopic, LearningRoadmap, StudentGoalInput


def _base(**overrides):
    values = dict(
        goal="Learn Java in 15 days",
        skill_level="Beginner",
        duration_value=15,
        duration_unit="Days",
        daily_time_value=2.0,
        daily_time_unit="Hours",
        learning_format="Mixed",
    )
    values.update(overrides)
    return StudentGoalInput(**values)


def test_valid_input_normalises_days_and_hours():
    data = _base()
    assert data.total_days == 15
    assert data.daily_hours == 2.0
    assert data.total_estimated_hours == 30.0


def test_weeks_and_minutes_convert():
    data = _base(duration_value=2, duration_unit="Weeks", daily_time_value=90.0, daily_time_unit="Minutes")
    assert data.total_days == 14
    assert data.daily_hours == 1.5
    assert data.total_estimated_hours == 21.0


def test_minutes_unit_allows_45_minutes():
    data = _base(daily_time_value=45.0, daily_time_unit="Minutes")
    assert data.daily_hours == 0.75


def test_invalid_skill_level_rejected():
    with pytest.raises(ValidationError):
        _base(skill_level="Master")


def test_invalid_format_rejected():
    with pytest.raises(ValidationError):
        _base(learning_format="Podcasts")


def test_zero_duration_rejected():
    with pytest.raises(ValidationError):
        _base(duration_value=0)


def test_hours_limit_is_per_unit():
    with pytest.raises(ValidationError):
        _base(daily_time_value=40.0, daily_time_unit="Hours")
    # 40 is fine when the unit is minutes.
    assert _base(daily_time_value=40.0, daily_time_unit="Minutes").daily_hours == 0.67


def test_daily_minutes_limit():
    with pytest.raises(ValidationError):
        _base(daily_time_value=1000.0, daily_time_unit="Minutes")


def _day(number):
    return DayTopic(
        day_number=number,
        topic_title=f"Topic {number}",
        estimated_time="1 Hour",
        concept_explanation="x",
    )


def test_duplicate_day_numbers_are_renumbered():
    roadmap = LearningRoadmap(
        title="T",
        goal="G",
        total_duration="2 Days",
        daily_commitment="1 Hour/Day",
        expected_outcome="O",
        days=[_day(3), _day(3), _day(7)],
    )
    assert [day.day_number for day in roadmap.days] == [1, 2, 3]


def test_gap_in_day_numbers_is_closed():
    roadmap = LearningRoadmap(
        title="T",
        goal="G",
        total_duration="2 Days",
        daily_commitment="1 Hour/Day",
        expected_outcome="O",
        days=[_day(2), _day(5)],
    )
    assert [day.day_number for day in roadmap.days] == [1, 2]


def test_progress_tracking():
    roadmap = LearningRoadmap(
        title="T",
        goal="G",
        total_duration="2 Days",
        daily_commitment="1 Hour/Day",
        expected_outcome="O",
        days=[_day(1), _day(2)],
    )
    assert roadmap.progress_percentage == 0.0
    roadmap.days[0].completed = True
    assert roadmap.progress_percentage == 50.0


def test_day_count_mismatch_is_visible():
    roadmap = LearningRoadmap(
        title="T",
        goal="G",
        total_duration="10 Days",
        daily_commitment="1 Hour/Day",
        expected_outcome="O",
        days=[_day(1)],
        requested_days=10,
    )
    assert roadmap.day_count_matches_request is False


def test_apply_completion_copies_state():
    roadmap = LearningRoadmap(
        title="T",
        goal="G",
        total_duration="2 Days",
        daily_commitment="1 Hour/Day",
        expected_outcome="O",
        days=[_day(1), _day(2)],
    )
    roadmap.apply_completion({2: True})
    assert roadmap.days[0].completed is False
    assert roadmap.days[1].completed is True
