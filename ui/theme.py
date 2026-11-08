"""Visual layer: CSS injection and small reusable render helpers."""

from __future__ import annotations

import html
from typing import Optional, Sequence, Tuple

import streamlit as st

CSS = """
<style>
:root {
  --lpg-bg: #ffffff;
  --lpg-muted: #f4f4f5;
  --lpg-border: #e4e4e7;
  --lpg-fg: #09090b;
  --lpg-fg-muted: #71717a;
  --lpg-accent: #18181b;
  --lpg-ring: rgba(37, 99, 235, 0.16);
  --lpg-radius: 10px;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--lpg-bg);
  color: var(--lpg-fg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, Helvetica, Arial, sans-serif;
}

header[data-testid="stHeader"] {
  /* Transparent, no blur: the frosted bar smeared the nav pill when it
     scrolled underneath. Keeping it clear leaves the nav readable. */
  background: transparent;
  backdrop-filter: none;
}

#MainMenu, footer,
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stStatusWidget"] { display: none !important; }

.block-container {
  max-width: 1080px;
  padding: 4.5rem 2.5rem 5rem 2.5rem;
}

h1, h2, h3, h4 {
  color: var(--lpg-fg);
  letter-spacing: -0.02em;
  font-weight: 600;
}
h1 { font-size: 1.9rem; }
h2 { font-size: 1.35rem; }
h3 { font-size: 1.1rem; }

section[data-testid="stSidebar"] {
  background: #fafafa;
  border-right: 1px solid var(--lpg-border);
}
section[data-testid="stSidebar"] .block-container {
  padding: 1.4rem 1.1rem 3rem 1.1rem;
  max-width: 100%;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { font-size: 0.95rem; }

/* ---------- buttons ---------- */
div.stButton > button,
div.stDownloadButton > button {
  border-radius: 8px;
  border: 1px solid var(--lpg-border);
  background: #ffffff;
  color: var(--lpg-fg);
  font-weight: 500;
  font-size: 0.875rem;
  padding: 0.45rem 0.9rem;
  min-height: 2.35rem;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.03);
  transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
}
div.stButton > button:hover,
div.stDownloadButton > button:hover {
  background: var(--lpg-muted);
  border-color: #d4d4d8;
  color: var(--lpg-fg);
}
div.stButton > button[kind="primary"] {
  background: var(--lpg-accent);
  border-color: var(--lpg-accent);
  color: #ffffff;
}
div.stButton > button[kind="primary"]:hover {
  background: #27272a;
  border-color: #27272a;
  color: #ffffff;
}
div.stButton > button:focus:not(:active) {
  box-shadow: 0 0 0 3px var(--lpg-ring);
  border-color: #a1a1aa;
}

/* ---------- inputs ---------- */
[data-testid="stTextInput"] .react-aria-TextField > div,
[data-testid="stNumberInput"] .react-aria-TextField > div,
[data-testid="stSelectbox"] .react-aria-ComboBox > div {
  background: #ffffff !important;
  border: 1px solid var(--lpg-border) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
[data-testid="stTextInput"] .react-aria-TextField > div:focus-within,
[data-testid="stNumberInput"] .react-aria-TextField > div:focus-within,
[data-testid="stSelectbox"] .react-aria-ComboBox > div:focus-within {
  border-color: #a1a1aa !important;
  box-shadow: 0 0 0 3px var(--lpg-ring) !important;
}
[role="listbox"] {
  background: #ffffff !important;
  border: 1px solid var(--lpg-border) !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08) !important;
  padding: 4px !important;
}
[role="option"] {
  border-radius: 6px !important;
}
[role="option"]:hover,
[role="option"][aria-selected="true"] {
  background: var(--lpg-muted) !important;
}

/* ---------- nav (st.segmented_control -> stButtonGroup) ---------- */
div[data-testid="stButtonGroup"] > div[role="radiogroup"] {
  background: var(--lpg-muted);
  border: 1px solid var(--lpg-border);
  border-radius: 10px;
  padding: 4px;
  gap: 2px;
  width: fit-content;
  margin-bottom: 1.6rem;
}
div[data-testid="stButtonGroup"] > div[role="radiogroup"] > button {
  border: 1px solid transparent !important;
  border-radius: 7px !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  color: var(--lpg-fg-muted) !important;
  padding: 0.35rem 0.9rem !important;
  background: transparent !important;
  box-shadow: none !important;
  min-height: 1.9rem;
  transition: background 120ms ease, color 120ms ease;
}
div[data-testid="stButtonGroup"] > div[role="radiogroup"] > button:hover {
  color: var(--lpg-fg) !important;
  background: rgba(0, 0, 0, 0.04) !important;
}
div[data-testid="stButtonGroup"] > div[role="radiogroup"] > button[aria-checked="true"] {
  background: #ffffff !important;
  color: var(--lpg-fg) !important;
  border-color: var(--lpg-border) !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.07) !important;
}
div[data-testid="stButtonGroup"] > div[role="radiogroup"] > button p {
  font-size: 0.85rem !important;
  font-weight: 500 !important;
}

/* ---------- containers ---------- */
[data-testid="stVerticalBlock"][class*="st-key-card_"],
[data-testid="stVerticalBlock"][class*="st-key-plan_"] {
  border: 1px solid var(--lpg-border) !important;
  border-radius: 12px !important;
  background: #ffffff;
}
div[data-testid="stExpander"] {
  border: 1px solid var(--lpg-border) !important;
  border-radius: 10px !important;
  background: #ffffff !important;
  box-shadow: none !important;
  margin-bottom: 0.6rem;
}
div[data-testid="stExpander"] summary {
  font-weight: 500;
  font-size: 0.9rem;
  padding: 0.55rem 0.85rem;
}
div[data-testid="stExpander"] summary:hover { color: var(--lpg-fg); }

/* ---------- metrics ---------- */
div[data-testid="stMetric"] {
  background: #ffffff;
  border: 1px solid var(--lpg-border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
}
[data-testid="stMetricLabel"] p {
  font-size: 0.72rem !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--lpg-fg-muted) !important;
  font-weight: 500 !important;
}
[data-testid="stMetricValue"] p {
  font-size: 1.35rem !important;
  font-weight: 600 !important;
  color: var(--lpg-fg) !important;
  line-height: 1.2 !important;
}

/* ---------- progress ---------- */
div[data-testid="stProgressBarTrack"] {
  background: var(--lpg-muted) !important;
  border-radius: 999px !important;
  overflow: hidden;
}
div[data-testid="stProgressBarTrack"] > div {
  background: var(--lpg-accent) !important;
  border-radius: 999px !important;
}

/* ---------- misc ---------- */
[data-testid="stCaptionContainer"] p {
  color: var(--lpg-fg-muted) !important;
  font-size: 0.82rem !important;
}
div[data-testid="stAlert"] {
  border-radius: 10px;
}
hr { border-color: var(--lpg-border); }
code {
  background: var(--lpg-muted);
  color: var(--lpg-fg);
  border-radius: 4px;
  padding: 0.1rem 0.3rem;
  font-size: 0.85em;
}
[data-testid="stCode"] code {
  background: transparent;
  color: inherit;
  padding: 0;
  font-size: 0.8rem;
}
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }

.lpg-brand {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-weight: 600;
  font-size: 0.98rem;
  letter-spacing: -0.01em;
  margin-bottom: 0.15rem;
}
.lpg-brand-mark {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #18181b;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
}
.lpg-eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--lpg-fg-muted);
  margin-bottom: 0.3rem;
}
.lpg-subtitle {
  color: var(--lpg-fg-muted);
  font-size: 0.92rem;
  line-height: 1.55;
  margin-bottom: 1.4rem;
}
.lpg-hint {
  color: var(--lpg-fg-muted);
  font-size: 0.82rem;
}
.lpg-tag {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--lpg-fg-muted);
  border: 1px solid var(--lpg-border);
  border-radius: 999px;
  padding: 0.05rem 0.5rem;
  margin-right: 0.35rem;
}
.lpg-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 500;
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  line-height: 1.5;
}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def brand() -> None:
    st.markdown(
        '<div class="lpg-brand"><span class="lpg-brand-mark">LP</span>'
        "Learning Path Generator</div>",
        unsafe_allow_html=True,
    )


def header(eyebrow: str, title: str, subtitle: Optional[str] = None) -> None:
    st.markdown(f'<div class="lpg-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f'<div class="lpg-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def hint(text: str) -> None:
    st.markdown(f'<div class="lpg-hint">{text}</div>', unsafe_allow_html=True)


def metrics(items: Sequence[Tuple[str, str]]) -> None:
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        with column:
            st.metric(label, value)


_BADGE_COLORS = {
    "connected": ("#ecfdf5", "#047857", "#a7f3d0"),
    "error": ("#fef2f2", "#b91c1c", "#fecaca"),
    "timeout": ("#fffbeb", "#b45309", "#fde68a"),
    "unconfigured": ("#f4f4f5", "#71717a", "#e4e4e7"),
    "idle": ("#f4f4f5", "#71717a", "#e4e4e7"),
}


def status_badge(label: str, status: str) -> None:
    bg, fg, border = _BADGE_COLORS.get(status, _BADGE_COLORS["idle"])
    st.markdown(
        f'<span class="lpg-badge" style="background:{bg};color:{fg};border-color:{border};">'
        f"{html.escape(str(label))}</span>",
        unsafe_allow_html=True,
    )


def pill(text: str) -> None:
    st.markdown(f'<span class="lpg-tag">{html.escape(str(text))}</span>', unsafe_allow_html=True)
