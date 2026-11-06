"""The built-in demo plan, loaded from assets/demo_roadmap.json."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from models import LearningRoadmap

_ASSET = Path(__file__).resolve().parent.parent / "assets" / "demo_roadmap.json"


@lru_cache(maxsize=1)
def _payload() -> str:
    return _ASSET.read_text(encoding="utf-8")


def load_demo_roadmap() -> LearningRoadmap:
    """Return a fresh copy so editing one session never leaks into another."""
    return LearningRoadmap.model_validate_json(_payload())
