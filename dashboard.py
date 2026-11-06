"""Application shell: page setup, sidebar, navigation and routing.

The heavy lifting lives in `ui/views/*`. This file only wires things together.
"""

from __future__ import annotations

import streamlit as st

import storage
from config import AppConfig
from openrouter_models import list_free_models, recommended_default
from ui import state, theme
from ui.views import about, connections, generate, library, roadmap


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_models():
    return list_free_models()


def _sidebar() -> None:
    session = st.session_state
    with st.sidebar:
        theme.brand()
        st.caption("A day-by-day plan that fits your week.")
        st.divider()

        st.markdown("**Access**")
        st.text_input(
            "OpenRouter API key",
            type="password",
            key="api_key_input",
            value=AppConfig.get_openrouter_api_key() or "",
            help="Create a free key at openrouter.ai/keys",
        )

        models = _cached_models()
        ids = [model.id for model in models]
        preferred = AppConfig.get_default_model()
        if preferred and preferred in ids:
            fallback = preferred
        else:
            recommended = recommended_default(models)
            fallback = recommended.id if recommended else (ids[0] if ids else "")
        if session.get("model_choice") not in ids:
            session.model_choice = fallback

        st.selectbox(
            "Free model",
            ids,
            key="model_choice",
            format_func=lambda model_id: next(
                (model.label for model in models if model.id == model_id), model_id
            ),
            help="Only free models are listed. Some handle long JSON better than others.",
        )
        if st.button("Refresh model list", use_container_width=True):
            _cached_models.clear()
            st.rerun()

        with st.expander("Custom model id"):
            st.text_input(
                "Model id",
                key="custom_model",
                placeholder="provider/model:free",
                help="Overrides the list above. Useful when a model is not listed yet.",
            )

        st.divider()
        with st.expander("MCP endpoints"):
            st.text_input(
                "YouTube MCP URL",
                key="yt_url",
                value=AppConfig.get_youtube_mcp_url() or "",
                placeholder="https://...pipedream.net/mcp",
            )
            st.text_input(
                "Google Drive MCP URL",
                key="drive_url",
                value=AppConfig.get_drive_mcp_url() or "",
                placeholder="https://...pipedream.net/mcp",
            )
            st.text_input(
                "Notion MCP URL",
                key="notion_url",
                value=AppConfig.get_notion_mcp_url() or "",
                placeholder="https://...pipedream.net/mcp",
            )
            st.caption("A URL alone is not a connection. Test it in the Connections tab.")

        st.divider()
        try:
            saved = storage.count_roadmaps()
        except Exception:
            saved = 0
        st.caption(f"{saved} plan(s) saved locally · data/app.db")


def _nav() -> str:
    session = st.session_state
    target = session.pop("target_nav", None)
    if target in state.NAV_ITEMS:
        # Recreate the widget so it starts from the requested tab.
        session.view = target
        session.nav_epoch = int(session.get("nav_epoch", 0)) + 1

    view = st.segmented_control(
        "Navigation",
        state.NAV_ITEMS,
        default=session.view,
        key=f"nav_{session.nav_epoch}",
        required=True,
        label_visibility="collapsed",
    )
    session.view = view
    return view


def _route(view: str) -> None:
    if view == "Generate":
        generate.render()
    elif view == "Roadmap":
        roadmap.render()
    elif view == "Library":
        library.render()
    elif view == "Connections":
        connections.render()
    else:
        about.render()


def main() -> None:
    st.set_page_config(
        page_title="Learning Path Generator",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme.inject()
    state.init()

    _sidebar()
    view = _nav()

    try:
        _route(view)
    except Exception as exc:  # noqa: BLE001 - keep the page usable
        st.error(f"Something went wrong on this page: {exc}")
        with st.expander("Details"):
            st.exception(exc)


if __name__ == "__main__":
    main()
