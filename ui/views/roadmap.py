"""Roadmap view: the active plan, progress and exports."""

from __future__ import annotations

import streamlit as st

import storage
from exporter import RoadmapExporter, safe_filename
from ui import state, theme
from ui.state import render_flash as state_render_flash
from youtube import thumbnail_url, video_id, watch_url


def _resource_meta(resource) -> str:
    parts = [resource.platform]
    if resource.channel_or_author:
        parts.append(resource.channel_or_author)
    if resource.is_mcp_verified:
        parts.append("MCP verified")
    return " · ".join(parts)


def _render_link_resource(resource) -> None:
    st.markdown(f"- [{resource.title}]({resource.url}) · {_resource_meta(resource)}")
    if resource.relevance_note:
        st.caption(resource.relevance_note)


def _render_video_resource(roadmap, day, index: int, resource, video: str) -> None:
    """Thumbnail card that swaps into an embedded player on click."""
    key = f"{roadmap.id}_{day.day_number}_{index}"
    watch = watch_url(video)

    if st.session_state.get("playing_video") == key:
        st.video(watch)
        st.caption(f"{resource.title} · {_resource_meta(resource)} · playing in the app")
        first, second, _ = st.columns([1, 1, 3])
        with first:
            if st.button("Close player", key=f"close_{key}", use_container_width=True):
                st.session_state.playing_video = None
                st.rerun()
        with second:
            st.link_button("Open on YouTube", watch, use_container_width=True)
        return

    thumb, info = st.columns([1, 2.4], gap="small")
    with thumb:
        st.image(
            thumbnail_url(video),
            alt=f"Thumbnail for {resource.title}",
            width="stretch",
        )
    with info:
        st.markdown(f"**{resource.title}**")
        st.caption(_resource_meta(resource))
        if resource.relevance_note:
            st.caption(resource.relevance_note)
        if st.button("▶ Watch here", key=f"play_{key}"):
            st.session_state.playing_video = key
            st.rerun()


def _render_resources(roadmap, day) -> None:
    if not day.resources:
        return
    st.markdown("**Resources**")
    for index, resource in enumerate(day.resources):
        video = video_id(resource.url)
        if video:
            _render_video_resource(roadmap, day, index, resource, video)
        else:
            _render_link_resource(resource)


def _render_day(roadmap, day, checked: bool) -> None:
    epoch = st.session_state.get("progress_epoch", 0)
    widget_key = f"chk_{roadmap.id}_{day.day_number}_{epoch}"

    def _toggle(day_number: int = day.day_number, key: str = widget_key) -> None:
        state.toggle(day_number, st.session_state.get(key, False))

    label = f"Day {day.day_number} · {day.topic_title}"
    with st.expander(label, expanded=not checked):
        st.checkbox("Mark this day done", value=checked, key=widget_key, on_change=_toggle)
        st.caption(day.estimated_time)
        st.write(day.concept_explanation)

        if day.key_takeaways:
            st.markdown("**Key takeaways**")
            for takeaway in day.key_takeaways:
                st.markdown(f"- {takeaway}")

        if day.resources:
            _render_resources(roadmap, day)

        if day.practice_exercises:
            st.markdown("**Practice**")
            for exercise in day.practice_exercises:
                st.markdown(f"- {exercise}")

        if day.assignment:
            st.info(f"**Assignment** — {day.assignment}")

        if day.revision_checkpoint:
            st.caption(f"Revision question: {day.revision_checkpoint}")


def _export_section(roadmap, completion) -> None:
    roadmap.apply_completion(completion)
    markdown = RoadmapExporter.to_markdown(roadmap)
    payload = RoadmapExporter.to_json(roadmap)

    st.markdown("### Export")
    first, second, third = st.columns(3)
    with first:
        st.download_button(
            "Download Markdown",
            data=markdown,
            file_name=safe_filename(roadmap.title, "md"),
            mime="text/markdown",
            use_container_width=True,
        )
    with second:
        st.download_button(
            "Download JSON",
            data=payload,
            file_name=safe_filename(roadmap.title, "json"),
            mime="application/json",
            use_container_width=True,
        )
    with third:
        if st.button("Save to Google Drive", use_container_width=True):
            if not state.drive_url():
                st.warning("Add your Google Drive MCP URL in the Connections tab first.")
            else:
                with st.spinner("Uploading through MCP..."):
                    result = RoadmapExporter.save_to_google_drive_mcp(roadmap, state.drive_url())
                if result.get("success"):
                    st.success(result.get("message", "Saved."))
                else:
                    st.error(result.get("message", "Could not save."))


def render() -> None:
    roadmap = state.current_roadmap()
    if roadmap is None:
        theme.header("Roadmap", "No plan open", "Generate a plan or open one from your library.")
        first, second, _ = st.columns([1, 1, 2])
        with first:
            if st.button("Generate a plan", type="primary", use_container_width=True):
                state.goto("Generate", rerun=True)
        with second:
            if st.button("Open library", use_container_width=True):
                state.goto("Library", rerun=True)
        return

    state_render_flash()
    completion = state.completion()
    roadmap.apply_completion(completion)

    if st.session_state.get("active_id") == state.DEMO_ID:
        theme.pill("Demo plan")

    st.markdown(f"## {roadmap.title}")
    st.caption(
        f"{roadmap.goal} · {roadmap.skill_level} · {roadmap.total_duration} · "
        f"{roadmap.daily_commitment}"
    )

    if roadmap.requested_days and roadmap.requested_days != len(roadmap.days):
        st.warning(
            f"You asked for {roadmap.requested_days} days, but this plan has "
            f"{len(roadmap.days)}. Regenerate with fewer days for a clean plan."
        )

    theme.metrics(
        [
            ("Duration", roadmap.total_duration),
            ("Days", f"{len(roadmap.days)}"),
            ("Completed", f"{roadmap.completed_count} / {len(roadmap.days)}"),
            ("Progress", f"{roadmap.progress_percentage:g}%"),
        ]
    )
    st.progress(roadmap.progress_percentage / 100.0)

    numbers = [day.day_number for day in roadmap.days]
    all_done, reset, spacer, new_plan = st.columns([1, 1, 2.4, 1.2])
    with all_done:
        if st.button("Mark all done", key="btn_mark_all", use_container_width=True):
            state.set_all(numbers, True)
            st.rerun()
    with reset:
        if st.button("Reset progress", key="btn_reset_all", use_container_width=True):
            state.set_all(numbers, False)
            st.rerun()
    with new_plan:
        if st.button("New plan", use_container_width=True):
            state.goto("Generate", rerun=True)

    st.divider()

    for day in roadmap.days:
        _render_day(roadmap, day, completion.get(day.day_number, False))

    if roadmap.capstone_project:
        st.divider()
        st.markdown("### Capstone project")
        st.markdown(f"**{roadmap.capstone_project.title}**")
        st.write(roadmap.capstone_project.description)
        for deliverable in roadmap.capstone_project.deliverables:
            st.markdown(f"- {deliverable}")

    if roadmap.next_steps:
        st.markdown("### Next steps")
        for step in roadmap.next_steps:
            st.markdown(f"- {step}")

    st.divider()
    _export_section(roadmap, completion)

    st.divider()
    with st.popover("Manage plan"):
        st.caption(f"Created {roadmap.created_at or 'this session'}.")
        if st.session_state.get("active_id") == state.DEMO_ID:
            if st.button("Close demo", use_container_width=True):
                state.clear_active()
                state.goto("Generate", rerun=True)
        else:
            st.write("Delete this plan permanently?")
            if st.button("Delete permanently", key="btn_delete_plan", type="primary", use_container_width=True):
                storage.delete_roadmap(roadmap.id)
                state.clear_active()
                state.goto("Library", rerun=True)
