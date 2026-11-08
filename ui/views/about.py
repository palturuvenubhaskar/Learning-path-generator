"""About view: how the app works and what it actually does."""

from __future__ import annotations

import streamlit as st

from config import MAX_PLAN_DAYS
from ui import theme


def render() -> None:
    theme.header(
        "About",
        "How this app works",
        "A short, honest description of the pipeline and its limits.",
    )

    st.markdown(
        f"""
### Pipeline

1. **Input** — the form builds a `StudentGoalInput`. Pydantic checks the level, format,
   duration and daily time. A limit is checked per unit: {MAX_PLAN_DAYS} days maximum,
   up to 16 hours or 960 minutes per day.
2. **Generation** — a free model on OpenRouter receives a strict prompt and returns one
   JSON object. Output is repaired once if it is malformed or truncated.
3. **Validation** — `LearningRoadmap` validates the JSON. Day numbers are forced to be
   unique and sequential, so progress keys can never collide.
4. **Optional MCP** — if a YouTube MCP URL is configured, the app searches each topic and
   adds the link it actually received. Only those links get the "MCP verified" label.
5. **Storage** — plans and checkboxes go into a local SQLite file (`data/app.db`).
6. **Export** — Markdown, JSON, or a file uploaded through your Drive MCP server.
"""
    )

    st.divider()
    st.markdown("### What is real, and what is a suggestion")
    st.markdown(
        "- **Verified links** come from a live MCP search. If the search fails, nothing is marked verified.\n"
        "- **All other links** are model suggestions. They may be wrong. Open them before trusting them.\n"
        "- **The YouTube badge** on a resource means one thing only: a search returned that URL."
    )

    st.divider()
    st.markdown("### Limits you should know")
    st.markdown(
        f"- Plans are capped at **{MAX_PLAN_DAYS} days**. Longer requests are shortened and flagged.\n"
        "- Free models are rate-limited and sometimes return broken JSON. The app retries once.\n"
        "- If the model returns fewer days than asked, the plan says so instead of pretending.\n"
        "- Progress is per plan and stored on this machine only."
    )

    st.divider()
    st.markdown("### Privacy")
    st.markdown(
        "- The API key is saved to `.env` on this machine when you enter it in the sidebar.\n"
        "- Plans are stored in `data/app.db` next to the app. Delete the file to wipe them.\n"
        "- Only the text you type in the form is sent to OpenRouter."
    )

    st.divider()
    st.markdown("### Running it")
    st.code(
        "python -m venv venv\n"
        "venv\\Scripts\\activate\n"
        "pip install -r requirements.txt\n"
        "streamlit run app.py",
        language="powershell",
    )
    st.caption("Paste a key in the sidebar; the app saves it to .env for next time.")
