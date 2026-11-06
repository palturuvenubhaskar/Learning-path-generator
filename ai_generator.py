"""
Roadmap generation through OpenRouter.

Free models vary a lot: some truncate long JSON, some wrap it in prose, some
skip fields. So this module is defensive:
  - it asks for one compact JSON object,
  - repairs malformed output once instead of failing,
  - fills required header fields from the request,
  - reports truncation and day-count mismatches instead of hiding them.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI
from pydantic import ValidationError

from config import MAX_PLAN_DAYS, OPENROUTER_BASE_URL
from models import LearningRoadmap, StudentGoalInput

ProgressCallback = Callable[[str, float], None]


class GenerationError(RuntimeError):
    """A generation failure with a message written for the person using the app."""


SCHEMA_EXAMPLE = """
{
  "title": "string",
  "goal": "string",
  "skill_level": "Beginner|Intermediate|Advanced",
  "total_duration": "e.g. 14 Days",
  "daily_commitment": "e.g. 2 Hours/Day",
  "expected_outcome": "string",
  "milestones": ["string"],
  "days": [
    {
      "day_number": 1,
      "topic_title": "string",
      "estimated_time": "e.g. 2 Hours",
      "concept_explanation": "2-4 sentences",
      "key_takeaways": ["string", "string"],
      "resources": [
        {"title": "string", "url": "https://...", "platform": "YouTube|Official Docs|GitHub|Web",
         "channel_or_author": "string or null", "relevance_note": "string", "is_mcp_verified": false}
      ],
      "practice_exercises": ["string", "string"],
      "assignment": "string",
      "revision_checkpoint": "string",
      "completed": false
    }
  ],
  "capstone_project": {"title": "string", "description": "string", "deliverables": ["string"]},
  "next_steps": ["string"]
}
"""

SYSTEM_PROMPT = f"""You are a senior curriculum designer and technical mentor.
You produce a day-by-day learning plan tailored to the student's goal, level and available time.

Rules:
1. Produce exactly the number of days requested. Number them 1..N in order.
2. Each day's workload must fit the student's daily time commitment.
3. Order topics from fundamentals to applied work. No gaps, no repeated days.
4. Every day needs: a concrete topic, a short concept explanation (2-4 sentences),
   2-3 key takeaways, 2-3 practice exercises, one assignment, one revision question.
5. Resources must be real, stable links (official docs, well-known channels).
   If you are not certain a URL exists, use a search URL like
   https://www.youtube.com/results?search_query=<topic> and set platform to "YouTube".
6. Set "is_mcp_verified" to false. The app sets it to true only after a live search.
7. End with one capstone project and 2-4 next steps.
8. Be compact. Short words. No filler. The whole answer must fit in one response.

Return ONE valid JSON object and nothing else. No markdown fences, no commentary.
The object must match this shape exactly:

{SCHEMA_EXAMPLE}
"""


def _strip_trailing_commas(text: str) -> str:
    """Remove commas before } or ] without touching commas inside strings."""
    out: List[str] = []
    in_string = False
    escaped = False
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        if char == ",":
            lookahead = index + 1
            while lookahead < length and text[lookahead] in " \t\r\n":
                lookahead += 1
            if lookahead < length and text[lookahead] in "}]":
                index += 1
                continue
        out.append(char)
        index += 1
    return "".join(out)


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Pull one JSON object out of a model response."""
    if not text or not text.strip():
        raise ValueError("The model returned an empty response")

    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
    if fence:
        cleaned = fence.group(1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in the response")
    cleaned = cleaned[start:end + 1]

    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        value = json.loads(_strip_trailing_commas(cleaned))

    if not isinstance(value, dict):
        raise ValueError("The response JSON is not an object")
    return value


class AILearningPathGenerator:
    """Calls an OpenRouter model and returns a validated LearningRoadmap."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: str = OPENROUTER_BASE_URL,
        client: Optional[OpenAI] = None,
        timeout: float = 180.0,
        max_retries: int = 2,
    ):
        if not api_key and client is None:
            raise GenerationError("An OpenRouter API key is required.")
        if not model_name:
            raise GenerationError("Choose a model before generating.")
        self.model_name = model_name
        self._client = client or OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            default_headers={
                "HTTP-Referer": "https://github.com/palturuvenubhaskar/Learning-path-generator",
                "X-Title": "Learning Path Generator",
            },
        )
        self.last_warnings: List[str] = []

    # ---------------------------------------------------------------- transport

    def _chat(self, messages: List[Dict[str, str]], temperature: float) -> tuple[str, str]:
        try:
            completion = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
            )
        except Exception as exc:  # noqa: BLE001 - translated below
            raise GenerationError(self._explain_error(exc)) from exc

        if not completion.choices:
            raise GenerationError("The model returned no choices. Try another free model.")
        choice = completion.choices[0]
        content = choice.message.content or ""
        finish_reason = getattr(choice, "finish_reason", "") or ""
        return content, finish_reason

    def _explain_error(self, exc: Exception) -> str:
        status = getattr(exc, "status_code", None)
        text = str(exc)
        if status == 401:
            return "OpenRouter rejected the API key (401). Check the key in the sidebar."
        if status == 402:
            return "OpenRouter says this model needs credits (402). Pick another free model."
        if status == 404:
            return f"Model '{self.model_name}' was not found on OpenRouter (404). Pick another model."
        if status == 429:
            return "OpenRouter rate limit reached (429). Wait a few seconds and try again."
        if status == 400 and "context" in text.lower():
            return "The request is too long for this model. Pick a model with a larger context window."
        if "timeout" in text.lower() or "timed out" in text.lower():
            return "The model took too long to answer. Try again, or pick a smaller model."
        if "connection" in text.lower():
            return "Could not reach OpenRouter. Check your internet connection."
        return f"Generation failed: {text[:400]}"

    # ------------------------------------------------------------------ parsing

    def _parse_or_repair(self, content: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            return extract_json_from_text(content)
        except Exception:
            pass

        if not content.strip():
            raise GenerationError("The model returned an empty response. Try another free model.")

        repair_messages = messages + [
            {"role": "assistant", "content": content[:14000]},
            {
                "role": "user",
                "content": (
                    "That reply was not valid JSON. Return only the corrected JSON object. "
                    "No markdown fences, no explanation, no trailing commas. Keep it compact."
                ),
            },
        ]
        repaired, _ = self._chat(repair_messages, temperature=0.0)
        try:
            return extract_json_from_text(repaired)
        except Exception as exc:
            raise GenerationError(
                "The model did not return valid JSON, even after a repair attempt. "
                "Free models handle long plans poorly; try fewer days or another model."
            ) from exc

    # --------------------------------------------------------------- generation

    def generate_roadmap(
        self,
        student_input: StudentGoalInput,
        progress_callback: Optional[ProgressCallback] = None,
        youtube_url: Optional[str] = None,
    ) -> LearningRoadmap:
        self.last_warnings = []
        requested_days = student_input.total_days
        target_days = min(requested_days, MAX_PLAN_DAYS)

        if requested_days > MAX_PLAN_DAYS:
            self.last_warnings.append(
                f"Plans are capped at {MAX_PLAN_DAYS} days; you asked for {requested_days}."
            )

        if progress_callback:
            progress_callback("Preparing the request...", 0.1)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_prompt(student_input, target_days)},
        ]

        if progress_callback:
            progress_callback(f"Asking {self.model_name} for the plan...", 0.25)

        content, finish_reason = self._chat(messages, temperature=0.3)

        if finish_reason == "length":
            self.last_warnings.append(
                "The model hit its output limit, so the plan may be short. Try fewer days."
            )
            if progress_callback:
                progress_callback("Output was truncated; asking for a more compact plan...", 0.45)
            retry_messages = messages + [
                {"role": "assistant", "content": content[:14000]},
                {
                    "role": "user",
                    "content": (
                        "Your answer was cut off. Return the complete JSON again, but much more "
                        "compact: max 2 takeaways and 2 exercises per day, one sentence for the "
                        "concept. Keep every day."
                    ),
                },
            ]
            content, finish_reason = self._chat(retry_messages, temperature=0.2)

        if progress_callback:
            progress_callback("Reading the plan...", 0.65)

        data = self._parse_or_repair(content, messages)
        data.setdefault("title", student_input.goal)
        data.setdefault("goal", student_input.goal)
        data.setdefault("skill_level", student_input.skill_level)
        data.setdefault("total_duration", f"{target_days} Days")
        data.setdefault("daily_commitment", f"{student_input.daily_hours:g} Hours/Day")
        data.setdefault("expected_outcome", "Practical, working knowledge of the subject.")
        data["created_at"] = data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
        data["requested_days"] = requested_days

        if progress_callback:
            progress_callback("Validating the structure...", 0.78)

        roadmap = self._validate(data, content, messages)

        if len(roadmap.days) != target_days:
            self.last_warnings.append(
                f"You asked for {target_days} days but the model returned {len(roadmap.days)}. "
                "Try again, or pick a stronger model."
            )

        if youtube_url and youtube_url.strip():
            if progress_callback:
                progress_callback("Searching YouTube through MCP...", 0.88)
            try:
                from mcp_client import MCPManager

                verified = MCPManager.enrich_roadmap_with_youtube(
                    roadmap,
                    youtube_url.strip(),
                    max_searches=min(8, len(roadmap.days)),
                    progress_callback=progress_callback,
                )
                if verified == 0:
                    self.last_warnings.append(
                        "YouTube MCP is configured but returned no usable links. "
                        "Resources stay AI-suggested and are not marked verified."
                    )
            except Exception as exc:  # noqa: BLE001
                self.last_warnings.append(f"YouTube MCP enrichment was skipped: {exc}")

        if progress_callback:
            progress_callback("Done.", 1.0)
        return roadmap

    @staticmethod
    def _build_user_prompt(student_input: StudentGoalInput, target_days: int) -> str:
        return f"""
Student request:
- Goal: {student_input.goal}
- Current level: {student_input.skill_level}
- Plan length: exactly {target_days} days
- Time per day: {student_input.daily_hours:g} hours ({student_input.daily_time_value:g} {student_input.daily_time_unit})
- Preferred format: {student_input.learning_format}
- Already known: {student_input.prior_knowledge or "nothing, starting from scratch"}
- Preferences: {student_input.learning_preferences or "standard comprehensive plan"}
- Final objective: {student_input.final_objective or "practical proficiency"}

Return the JSON object for these {target_days} days.
""".strip()

    def _validate(self, data: Dict[str, Any], content: str, messages: List[Dict[str, str]]) -> LearningRoadmap:
        try:
            return LearningRoadmap.model_validate(data)
        except ValidationError as exc:
            repair_messages = messages + [
                {"role": "assistant", "content": json.dumps(data, ensure_ascii=False)[:14000]},
                {
                    "role": "user",
                    "content": (
                        "This JSON failed validation with the following errors:\n"
                        f"{exc}\n\nReturn the corrected complete JSON object only."
                    ),
                },
            ]
            repaired, _ = self._chat(repair_messages, temperature=0.0)
            repaired_data = self._parse_or_repair(repaired, messages)
            repaired_data.setdefault("created_at", data.get("created_at"))
            repaired_data.setdefault("requested_days", data.get("requested_days"))
            try:
                return LearningRoadmap.model_validate(repaired_data)
            except ValidationError as second:  # pragma: no cover - defensive
                raise GenerationError(
                    f"The model's plan did not match the required schema: {second}"
                ) from second
