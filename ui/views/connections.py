"""Connections view: MCP server health checks and discovered tools."""

from __future__ import annotations

import streamlit as st

from mcp_client import MCPManager
from ui import state, theme

SERVERS = [
    ("youtube", "YouTube", "Searches real tutorials and marks links as verified."),
    ("drive", "Google Drive", "Saves the exported Markdown file to your Drive."),
    ("notion", "Notion", "Optional page export target."),
]


def _url_for(name: str) -> str:
    return {
        "youtube": state.youtube_url,
        "drive": state.drive_url,
        "notion": state.notion_url,
    }[name]()


def render() -> None:
    theme.header(
        "Connections",
        "MCP servers",
        "Optional. Without these the app still works: links stay AI-suggested and exports are local.",
    )

    for name, label, description in SERVERS:
        url = _url_for(name)
        with st.container(border=True, key=f"card_{name}"):
            top_left, top_right = st.columns([4, 1])
            with top_left:
                st.markdown(f"**{label}**")
                st.caption(description)
                if url:
                    st.code(url, language=None)
                else:
                    st.caption("Not configured. Add the URL in the sidebar.")
            with top_right:
                if st.button("Test", key=f"test_{name}", use_container_width=True, disabled=not url):
                    with st.spinner("Connecting..."):
                        result = MCPManager.test_server_connection_sync(name, url)
                    st.session_state.mcp_status[name] = result
                    st.rerun()

            result = (st.session_state.get("mcp_status") or {}).get(name)
            if result:
                theme.status_badge(
                    f"{result.get('status', 'unknown')} — {result.get('message', '')}",
                    result.get("status", "idle"),
                )
                tools = result.get("tools") or []
                if tools:
                    st.caption("Tools: " + ", ".join(f"`{tool}`" for tool in tools))

    st.divider()
    st.markdown("### How to connect")
    st.markdown(
        "1. Create an MCP server at [pipedream.com](https://pipedream.com/) and authorize the app.\n"
        "2. Copy its streamable HTTP URL (usually ends in `/mcp`).\n"
        "3. Paste it into the sidebar, then press **Test** here.\n"
        "4. A green badge means the server answered and listed its tools."
    )
    st.caption(
        "A URL in the sidebar is not a connection. The badge only turns green after a real "
        "health check succeeds."
    )
