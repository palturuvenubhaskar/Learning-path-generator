"""Generate view: the request form and the generation run."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Tuple

import streamlit as st
from pydantic import ValidationError

import storage
from ai_generator import AILearningPathGenerator, GenerationError
from config import MAX_PLAN_DAYS
from models import ALLOWED_FORMATS, ALLOWED_SKILL_LEVELS, MAX_DAILY_HOURS, StudentGoalInput
from ui import state, theme
from ui.demo_data import load_demo_roadmap

PRESETS = [
    (
        "Python · data",
        dict(
            goal="Master Python for data analysis",
            skill="Beginner",
            dur_unit="Days",
            dur_val=14,
            time_unit="Hours",
            time_val=2.0,
            fmt="Mixed",
        ),
    ),
    (
        "System design",
        dict(
            goal="System design and distributed architecture",
            skill="Advanced",
            dur_unit="Days",
            dur_val=10,
            time_unit="Hours",
            time_val=2.5,
            fmt="Documentation",
        ),
    ),
    (
        "React + Node",
        dict(
            goal="Full-stack web development with React, TypeScript and Node.js",
            skill="Intermediate",
            dur_unit="Days",
            dur_val=21,
            time_unit="Hours",
            time_val=3.0,
            fmt="Projects",
        ),
    ),
    (
        "DevOps",
        dict(
            goal="DevOps: Docker, CI/CD pipelines and Kubernetes",
            skill="Intermediate",
            dur_unit="Days",
            dur_val=14,
            time_unit="Hours",
            time_val=2.0,
            fmt="Exercises",
        ),
    ),
]


def _apply_preset(
    goal: str,
    skill: str,
    dur_unit: str,
    dur_val: int,
    time_unit: str,
    time_val: float,
    fmt: str,
) -> None:
    session = st.session_state
    session.goal = goal
    session.skill = skill
    session.dur_unit = dur_unit
    session.dur_val = dur_val
    session.time_unit = time_unit
    session.time_val = time_val
    session.fmt = fmt


def _on_duration_unit_change() -> None:
    st.session_state.dur_val = 2 if st.session_state.dur_unit == "Weeks" else 14


def _on_time_unit_change() -> None:
    st.session_state.time_val = 60.0 if st.session_state.time_unit == "Minutes" else 2.0


def _time_bounds(unit: str) -> Tuple[float, float, float]:
    if unit == "Minutes":
        return 5.0, 960.0, 5.0
    return 0.25, MAX_DAILY_HOURS, 0.25


def _duration_max(unit: str) -> int:
    return max(1, MAX_PLAN_DAYS // 7) if unit == "Weeks" else MAX_PLAN_DAYS


def _summary() -> None:
    days = st.session_state.dur_val * 7 if st.session_state.dur_unit == "Weeks" else st.session_state.dur_val
    hours = st.session_state.time_val / 60.0 if st.session_state.time_unit == "Minutes" else st.session_state.time_val
    total_hours = round(days * hours, 1)
    finish = date.today() + timedelta(days=days)
    theme.metrics(
        [
            ("Days", f"{days}"),
            ("Hours / day", f"{hours:g}"),
            ("Total hours", f"{total_hours:g}"),
            ("Finish by", finish.strftime("%d %b")),
        ]
    )


def _run_generation() -> None:
    if not state.api_key():
        st.error("Add your OpenRouter API key in the sidebar first.")
        return
    if not state.model_id():
        st.error("Pick a free model in the sidebar first.")
        return

    try:
        payload = StudentGoalInput(
            goal=st.session_state.goal,
            skill_level=st.session_state.skill,
            duration_value=int(st.session_state.dur_val),
            duration_unit=st.session_state.dur_unit,
            daily_time_value=float(st.session_state.time_val),
            daily_time_unit=st.session_state.time_unit,
            learning_format=st.session_state.fmt,
            prior_knowledge=st.session_state.prior.strip() or None,
            learning_preferences=st.session_state.prefs.strip() or None,
            final_objective=st.session_state.objective.strip() or None,
        )
    except ValidationError as exc:
        first = exc.errors()[0]
        st.error(f"{first.get('loc', ('input',))[0]}: {first.get('msg', 'invalid value')}")
        return

    bar = st.progress(0.0)
    status = st.empty()

    def on_progress(message: str, progress: float) -> None:
        bar.progress(max(0.0, min(1.0, progress)))
        status.caption(message)

    try:
        generator = AILearningPathGenerator(api_key=state.api_key(), model_name=state.model_id())
        with st.spinner("Working on your plan..."):
            roadmap = generator.generate_roadmap(
                payload,
                progress_callback=on_progress,
                youtube_url=state.youtube_url() or None,
            )
    except GenerationError as exc:
        bar.empty()
        status.empty()
        st.error(str(exc))
        return
    except Exception as exc:  # noqa: BLE001
        bar.empty()
        status.empty()
        st.error(f"Unexpected error: {exc}")
        return

    storage.save_roadmap(roadmap, {})
    state.set_active(roadmap, {})
    state.flash(generator.last_warnings)
    state.goto("Roadmap", rerun=True)


def render() -> None:
    theme.header(
        "New plan",
        "Design a learning plan",
        "Describe what you want to learn and how much time you have. The plan is built day by day.",
    )

    preset_columns = st.columns(len(PRESETS))
    for column, (label, values) in zip(preset_columns, PRESETS):
        with column:
            st.button(
                label,
                key=f"preset_{label}",
                on_click=_apply_preset,
                kwargs=values,
                use_container_width=True,
            )

    st.divider()

    st.text_input(
        "What do you want to learn?",
        key="goal",
        placeholder="e.g. Master Python for data analysis",
    )

    first, second = st.columns(2)
    with first:
        st.selectbox("Current level", ALLOWED_SKILL_LEVELS, key="skill")
    with second:
        st.selectbox("Preferred format", ALLOWED_FORMATS, key="fmt")

    st.markdown("**Schedule**")
    duration_col, duration_value_col = st.columns(2)
    with duration_col:
        st.selectbox(
            "Duration unit",
            ["Days", "Weeks"],
            key="dur_unit",
            on_change=_on_duration_unit_change,
        )
    with duration_value_col:
        st.number_input(
            "Duration",
            min_value=1,
            max_value=_duration_max(st.session_state.dur_unit),
            step=1,
            key="dur_val",
            help=f"Plans are capped at {MAX_PLAN_DAYS} days.",
        )

    time_unit_col, time_value_col = st.columns(2)
    with time_unit_col:
        st.selectbox(
            "Daily time unit",
            ["Hours", "Minutes"],
            key="time_unit",
            on_change=_on_time_unit_change,
        )
    with time_value_col:
        low, high, step = _time_bounds(st.session_state.time_unit)
        st.number_input(
            "Daily time",
            min_value=low,
            max_value=high,
            step=step,
            key="time_val",
        )

    with st.expander("Advanced options"):
        st.text_input("Topics you already know", key="prior", placeholder="e.g. basic syntax, Git")
        st.text_input("Preferences or constraints", key="prefs", placeholder="e.g. more code examples, no videos")
        st.text_input("Final objective", key="objective", placeholder="e.g. interview prep, portfolio project")

    st.divider()
    _summary()
    st.write("")

    left, right = st.columns([2, 1])
    with left:
        if st.button("Generate plan", type="primary", use_container_width=True):
            _run_generation()
    with right:
        if st.button("Load demo plan", use_container_width=True):
            state.set_active_demo(load_demo_roadmap())
            state.goto("Roadmap", rerun=True)

    if state.youtube_url():
        theme.hint(
            "YouTube MCP is configured. After the plan is generated, real tutorial links are "
            "searched and marked as verified. This adds a few seconds."
        )
