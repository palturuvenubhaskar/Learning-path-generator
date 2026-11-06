"""Tests for JSON extraction, repair, truncation handling and error mapping."""

import json
from types import SimpleNamespace

import pytest

from ai_generator import AILearningPathGenerator, GenerationError, extract_json_from_text
from models import StudentGoalInput
from openrouter_models import is_free_model, parse_models
from exporter import safe_filename


VALID_PLAN = {
    "title": "15-Day Java Mastery",
    "goal": "Learn Java",
    "skill_level": "Beginner",
    "total_duration": "15 Days",
    "daily_commitment": "2 Hours/Day",
    "expected_outcome": "Build apps",
    "milestones": ["OOP by day 7"],
    "days": [
        {
            "day_number": 1,
            "topic_title": "Setup",
            "estimated_time": "2 Hours",
            "concept_explanation": "Install the JDK.",
            "key_takeaways": ["JVM"],
            "resources": [],
            "practice_exercises": ["Hello world"],
            "assignment": "Install JDK",
            "revision_checkpoint": "What is bytecode?",
            "completed": False,
        }
    ],
    "capstone_project": {"title": "CLI app", "description": "Build it", "deliverables": ["Code"]},
    "next_steps": ["Spring"],
}


class FakeAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def completion(content, finish_reason="stop"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)]
    )


class FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        response = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(response, Exception):
            raise response
        return response


class FakeClient:
    def __init__(self, responses):
        self.completions = FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


def make_generator(responses):
    return AILearningPathGenerator(
        api_key="test",
        model_name="test/model:free",
        client=FakeClient(responses),
    )


def student(days=15):
    return StudentGoalInput(
        goal="Learn Java",
        duration_value=days,
        duration_unit="Days",
        daily_time_value=2.0,
        daily_time_unit="Hours",
    )


def test_extract_from_markdown_fence():
    raw = "Here you go:\n```json\n" + json.dumps(VALID_PLAN) + "\n```\nEnjoy"
    assert extract_json_from_text(raw)["title"] == "15-Day Java Mastery"


def test_extract_plain_json():
    assert extract_json_from_text(json.dumps(VALID_PLAN))["goal"] == "Learn Java"


def test_extract_repairs_trailing_comma():
    raw = '{"a": 1, "b": [1, 2,],}'
    assert extract_json_from_text(raw) == {"a": 1, "b": [1, 2]}


def test_extract_keeps_commas_inside_strings():
    raw = '{"a": "x, }", "b": 2}'
    assert extract_json_from_text(raw)["a"] == "x, }"


def test_generation_returns_validated_roadmap():
    generator = make_generator([completion(json.dumps(VALID_PLAN))])
    roadmap = generator.generate_roadmap(student(1))
    assert roadmap.title == "15-Day Java Mastery"
    assert len(roadmap.days) == 1
    assert roadmap.requested_days == 1


def test_generation_repairs_broken_json():
    generator = make_generator([completion("not json at all"), completion(json.dumps(VALID_PLAN))])
    roadmap = generator.generate_roadmap(student(1))
    assert roadmap.title == "15-Day Java Mastery"
    assert generator.last_warnings == []
    assert len(generator._client.completions.calls) == 2


def test_truncated_output_triggers_compact_retry():
    generator = make_generator(
        [completion(json.dumps(VALID_PLAN), finish_reason="length"), completion(json.dumps(VALID_PLAN))]
    )
    generator.generate_roadmap(student(1))
    assert any("output limit" in warning for warning in generator.last_warnings)


def test_day_count_mismatch_is_warned():
    generator = make_generator([completion(json.dumps(VALID_PLAN))])
    generator.generate_roadmap(student(10))
    assert any("10 days" in warning for warning in generator.last_warnings)


def test_empty_response_is_an_error():
    generator = make_generator([completion("")])
    with pytest.raises(GenerationError):
        generator.generate_roadmap(student(1))


@pytest.mark.parametrize(
    "status,expected",
    [
        (401, "401"),
        (402, "402"),
        (404, "404"),
        (429, "429"),
    ],
)
def test_http_errors_are_explained(status, expected):
    generator = make_generator([FakeAPIError("boom", status_code=status)])
    with pytest.raises(GenerationError) as info:
        generator.generate_roadmap(student(1))
    assert expected in str(info.value)


def test_expects_api_key():
    with pytest.raises(GenerationError):
        AILearningPathGenerator(api_key="", model_name="m")


def test_free_model_detection():
    assert is_free_model({"id": "x:free"})
    assert is_free_model({"id": "y", "pricing": {"prompt": "0", "completion": "0"}})
    assert not is_free_model({"id": "z", "pricing": {"prompt": "0.1", "completion": "0.2"}})


def test_parse_models_keeps_only_free_and_sorts_by_context():
    payload = {
        "data": [
            {"id": "a:free", "name": "A", "context_length": 8000},
            {"id": "b", "name": "B", "context_length": 128000, "pricing": {"prompt": "0", "completion": "0"}},
            {"id": "paid", "name": "Paid", "context_length": 200000, "pricing": {"prompt": "1", "completion": "2"}},
        ]
    }
    models = parse_models(payload)
    assert [model.id for model in models] == ["b", "a:free"]


def test_safe_filename_strips_illegal_characters():
    assert safe_filename('A: B/C*? "x"', "md") == "A_BC_x.md"
    assert safe_filename("", "json", fallback="plan") == "plan.json"
