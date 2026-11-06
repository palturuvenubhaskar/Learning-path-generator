"""Library view: saved plans."""

from __future__ import annotations

import streamlit as st

import storage
from ui import state, theme


def render() -> None:
    theme.header("Library", "Your plans", "Saved locally in a small SQLite database.")

    plans = storage.list_roadmaps()
    if not plans:
        st.info("No saved plans yet. Generate one, or open the demo from the Generate tab.")
        if st.button("Generate a plan", type="primary"):
            state.goto("Generate", rerun=True)
        return

    for plan in plans:
        with st.container(border=True, key=f"plan_{plan['id']}"):
            first, second, third = st.columns([5, 1, 1])
            with first:
                st.markdown(f"**{plan['title']}**")
                st.caption(
                    f"{plan['goal']} · {plan['day_count']} days · "
                    f"{plan['completed']} done · updated {plan['updated_at']}"
                )
            with second:
                if st.button("Open", key=f"open_{plan['id']}", use_container_width=True):
                    loaded = storage.get_roadmap(plan["id"])
                    if loaded is None:
                        st.error("That plan could not be loaded.")
                    else:
                        roadmap, completion = loaded
                        state.set_active(roadmap, completion)
                        state.goto("Roadmap", rerun=True)
            with third:
                with st.popover("Delete", use_container_width=True):
                    st.write("Delete permanently?")
                    if st.button("Yes, delete", key=f"del_{plan['id']}", type="primary"):
                        storage.delete_roadmap(plan["id"])
                        if st.session_state.get("active_id") == plan["id"]:
                            state.clear_active()
                        st.rerun()
