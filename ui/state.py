"""Session state helpers: active plan, navigation, API settings, flash messages."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

import storage
from models import LearningRoadmap

DEMO_ID = "__demo__"

NAV_ITEMS = ["Generate", "Roadmap", "Library", "Connections", "About"]


def init() -> None:
    ss = st.session_state
    ss.setdefault("view", NAV_ITEMS[0])
    ss.setdefault("nav_epoch", 0)
    ss.setdefault("target_nav", None)
    ss.setdefault("active_id", None)
    ss.setdefault("roadmap_json", None)
    ss.setdefault("completion", {})
    ss.setdefault("progress_epoch", 0)
    ss.setdefault("flash", [])
    ss.setdefault("mcp_status", {})
    ss.setdefault("confirm_delete", False)

    # Widget defaults. Setting these before the widgets exist is allowed.
    ss.setdefault("goal", "Master Python for data analysis")
    ss.setdefault("skill", "Beginner")
    ss.setdefault("fmt", "Mixed")
    ss.setdefault("dur_unit", "Days")
    ss.setdefault("dur_val", 14)
    ss.setdefault("time_unit", "Hours")
    ss.setdefault("time_val", 2.0)
    ss.setdefault("prior", "")
    ss.setdefault("prefs", "")
    ss.setdefault("objective", "")
    ss.setdefault("custom_model", "")

    if ss.get("active_id") is None:
        _restore_from_query()


def _restore_from_query() -> None:
    """A page refresh starts a new session; the plan id in the URL restores it."""
    try:
        plan_id = st.query_params.get("plan")
    except Exception:
        plan_id = None
    if not plan_id:
        return
    loaded = storage.get_roadmap(str(plan_id))
    if loaded is None:
        return
    roadmap, completion = loaded
    st.session_state.active_id = roadmap.id
    st.session_state.roadmap_json = roadmap.model_dump_json()
    st.session_state.completion = completion


def goto(view: str, rerun: bool = False) -> None:
    """Queue navigation for the start of the next run.

    `nav` belongs to the nav widget, so it cannot be written after that widget
    is created. `target_nav` is consumed by `_nav()` before the widget exists.
    """
    if view in NAV_ITEMS:
        st.session_state.target_nav = view
    if rerun:
        st.rerun()


# ------------------------------------------------------------------ settings


def api_key() -> str:
    return (st.session_state.get("api_key_input") or "").strip()


def model_id() -> str:
    custom = (st.session_state.get("custom_model") or "").strip()
    if custom:
        return custom
    return (st.session_state.get("model_choice") or "").strip()


def youtube_url() -> str:
    return (st.session_state.get("yt_url") or "").strip()


def drive_url() -> str:
    return (st.session_state.get("drive_url") or "").strip()


def notion_url() -> str:
    return (st.session_state.get("notion_url") or "").strip()


# -------------------------------------------------------------------- plans


def current_roadmap() -> Optional[LearningRoadmap]:
    raw = st.session_state.get("roadmap_json")
    if not raw:
        return None
    try:
        return LearningRoadmap.model_validate_json(raw)
    except Exception:
        return None


def completion() -> Dict[int, bool]:
    return dict(st.session_state.get("completion") or {})


def bump_epoch() -> None:
    """Invalidate day-checkbox widget keys so a new plan renders its own values."""
    st.session_state.progress_epoch = int(st.session_state.get("progress_epoch", 0)) + 1


def set_active(roadmap: LearningRoadmap, completion_state: Optional[Dict[int, bool]] = None, persist_url: bool = True) -> None:
    st.session_state.active_id = roadmap.id
    st.session_state.roadmap_json = roadmap.model_dump_json()
    st.session_state.completion = dict(completion_state or {})
    bump_epoch()
    if persist_url:
        try:
            st.query_params["plan"] = roadmap.id
        except Exception:
            pass


def set_active_demo(roadmap: LearningRoadmap) -> None:
    st.session_state.active_id = DEMO_ID
    st.session_state.roadmap_json = roadmap.model_dump_json()
    st.session_state.completion = {}
    bump_epoch()
    try:
        st.query_params.pop("plan", None)
    except Exception:
        pass


def clear_active() -> None:
    st.session_state.active_id = None
    st.session_state.roadmap_json = None
    st.session_state.completion = {}
    bump_epoch()
    try:
        st.query_params.pop("plan", None)
    except Exception:
        pass


def toggle(day_number: int, value: bool) -> None:
    state = completion()
    state[int(day_number)] = bool(value)
    st.session_state.completion = state
    active = st.session_state.get("active_id")
    if active and active != DEMO_ID:
        storage.save_completion(active, state)


def set_all(day_numbers: List[int], value: bool) -> None:
    active = st.session_state.get("active_id")
    if not active:
        return
    state = completion()
    for number in day_numbers:
        state[int(number)] = value
    st.session_state.completion = state
    # Bump the epoch so the day checkboxes are rebuilt with the new values.
    # Streamlit ignores a widget's `value=` once its key exists in session state.
    st.session_state.progress_epoch = int(st.session_state.get("progress_epoch", 0)) + 1
    if active != DEMO_ID:
        storage.save_completion(active, state)


# -------------------------------------------------------------------- flash


def flash(messages: Any) -> None:
    if not messages:
        return
    if isinstance(messages, str):
        messages = [messages]
    st.session_state.flash = list(messages)


def render_flash() -> None:
    messages: List[str] = st.session_state.get("flash") or []
    for message in messages:
        st.warning(message)
    st.session_state.flash = []
