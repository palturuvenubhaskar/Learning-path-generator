"""Tests for local SQLite persistence."""

import config
import storage
from models import DayTopic, LearningRoadmap


def _roadmap():
    return LearningRoadmap(
        title="Test plan",
        goal="Test goal",
        total_duration="2 Days",
        daily_commitment="1 Hour/Day",
        expected_outcome="Outcome",
        days=[
            DayTopic(
                day_number=number,
                topic_title=f"Topic {number}",
                estimated_time="1 Hour",
                concept_explanation="x",
            )
            for number in (1, 2)
        ],
        created_at="2026-01-01 10:00",
    )


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    roadmap = _roadmap()
    storage.save_roadmap(roadmap, {1: True})

    loaded = storage.get_roadmap(roadmap.id)
    assert loaded is not None
    stored, completion = loaded
    assert stored.title == "Test plan"
    assert completion == {1: True}


def test_completion_updates_and_listing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    roadmap = _roadmap()
    storage.save_roadmap(roadmap, {})
    storage.save_completion(roadmap.id, {1: True, 2: True})

    plans = storage.list_roadmaps()
    assert len(plans) == 1
    assert plans[0]["completed"] == 2
    assert plans[0]["day_count"] == 2


def test_save_is_an_upsert(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    roadmap = _roadmap()
    storage.save_roadmap(roadmap, {})
    roadmap.title = "Renamed"
    storage.save_roadmap(roadmap, {})
    assert storage.count_roadmaps() == 1
    assert storage.list_roadmaps()[0]["title"] == "Renamed"


def test_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    roadmap = _roadmap()
    storage.save_roadmap(roadmap, {})
    storage.delete_roadmap(roadmap.id)
    assert storage.count_roadmaps() == 0
    assert storage.get_roadmap(roadmap.id) is None


def test_missing_plan_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    assert storage.get_roadmap("does-not-exist") is None
