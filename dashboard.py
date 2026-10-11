"""
AI Learning Path Generator - Streamlit Dashboard
Red Noir Visual Design System (Google Gemini & Model Context Protocol • MCP)
"""

import streamlit as st
import asyncio
from datetime import datetime

from config import AppConfig
from models import StudentGoalInput, LearningRoadmap
from ai_generator import AILearningPathGenerator
from mcp_client import MCPManager
from exporter import RoadmapExporter


def main():
    # Page configuration
    st.set_page_config(
        page_title="Learning Path Generator",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Red Noir Aesthetic Design System Injection
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">

    <style>
        :root {
            --accent-red: #ef233c;
            --accent-red-glow: rgba(239, 35, 60, 0.45);
            --bg-deep: #000000;
            --bg-card: rgba(18, 18, 22, 0.75);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(239, 35, 60, 0.4);
            --text-primary: #ffffff;
            --text-secondary: #a1a1aa;
        }

        /* Selection styling */
        ::selection {
            background: #ef233c !important;
            color: #ffffff !important;
        }

        /* Global App Atmosphere */
        .stApp {
            background-color: #000000 !important;
            background-image: 
                radial-gradient(circle at 50% 0%, rgba(239, 35, 60, 0.08) 0%, transparent 60%),
                linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px) !important;
            background-size: 100% 100%, 40px 40px, 40px 40px !important;
            color: #f4f4f5 !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #08080a !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3 {
            font-family: 'Manrope', sans-serif !important;
            color: #ffffff !important;
            letter-spacing: -0.02em !important;
        }

        /* Typography & Headers */
        .main-title {
            font-family: 'Manrope', sans-serif;
            font-size: 2.6rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1.15;
            background: linear-gradient(180deg, #ffffff 0%, rgba(255, 255, 255, 0.7) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.35rem;
        }
        .main-title span.accent-red {
            color: #ef233c;
            -webkit-text-fill-color: #ef233c;
            text-shadow: 0 0 25px rgba(239, 35, 60, 0.5);
        }
        .brand-diamond {
            width: 14px;
            height: 14px;
            background: #ef233c;
            transform: rotate(45deg);
            display: inline-block;
            margin-right: 10px;
            box-shadow: 0 0 16px rgba(239, 35, 60, 0.8);
            border-radius: 2px;
            vertical-align: middle;
        }
        .sub-title {
            color: #a1a1aa;
            font-size: 1.05rem;
            font-weight: 400;
            line-height: 1.6;
            margin-bottom: 1.8rem;
        }

        /* Live Red Ping Badge */
        .badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 9999px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            font-family: 'Manrope', sans-serif;
            font-size: 0.8rem;
            font-weight: 600;
            color: #f4f4f5;
        }
        .pulse-dot-container {
            position: relative;
            display: flex;
            width: 8px;
            height: 8px;
        }
        .pulse-ping {
            position: absolute;
            display: inline-flex;
            height: 100%;
            width: 100%;
            border-radius: 9999px;
            background-color: #ef233c;
            opacity: 0.75;
            animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
        .pulse-solid {
            position: relative;
            display: inline-flex;
            border-radius: 9999px;
            height: 8px;
            width: 8px;
            background-color: #ef233c;
            box-shadow: 0 0 8px #ef233c;
        }
        @keyframes ping {
            75%, 100% {
                transform: scale(2.2);
                opacity: 0;
            }
        }

        /* Metric Cards */
        .metric-card {
            background: rgba(18, 18, 22, 0.7);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 20px 16px;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #ef233c, transparent);
            opacity: 0.4;
            transition: opacity 0.3s ease;
        }
        .metric-card:hover {
            border-color: rgba(239, 35, 60, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 25px rgba(239, 35, 60, 0.15);
        }
        .metric-card:hover::before {
            opacity: 1;
        }
        .metric-val {
            font-family: 'Manrope', sans-serif;
            font-size: 1.85rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.02em;
        }
        .metric-label {
            font-size: 0.75rem;
            color: #71717a;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
            margin-top: 4px;
        }

        /* Form Container */
        div[data-testid="stForm"] {
            background: rgba(14, 14, 18, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            padding: 26px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
        }

        /* Input Controls */
        input, select, textarea, div[data-baseweb="select"] {
            background-color: rgba(10, 10, 14, 0.9) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
        }
        input:focus, textarea:focus {
            border-color: #ef233c !important;
            box-shadow: 0 0 15px rgba(239, 35, 60, 0.3) !important;
        }

        /* Primary Button - Red Noir Shiny CTA */
        div.stButton > button[kind="primary"],
        div[data-testid="stForm"] button[kind="primary"] {
            background: linear-gradient(135deg, #ef233c 0%, #b91c1c 100%) !important;
            color: #ffffff !important;
            font-family: 'Manrope', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.02em !important;
            border: 1px solid rgba(239, 35, 60, 0.8) !important;
            border-radius: 9999px !important;
            padding: 0.65rem 2rem !important;
            box-shadow: 0 0 25px rgba(239, 35, 60, 0.35) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stForm"] button[kind="primary"]:hover {
            background: linear-gradient(135deg, #ff3b53 0%, #d90429 100%) !important;
            box-shadow: 0 0 35px rgba(239, 35, 60, 0.65) !important;
            transform: translateY(-1px) scale(1.01) !important;
            border-color: #ef233c !important;
        }

        /* Secondary / Standard Buttons */
        div.stButton > button:not([kind="primary"]) {
            background: rgba(24, 24, 27, 0.8) !important;
            color: #e4e4e7 !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 9999px !important;
            transition: all 0.25s ease !important;
        }
        div.stButton > button:not([kind="primary"]):hover {
            background: rgba(39, 39, 42, 0.9) !important;
            border-color: rgba(239, 35, 60, 0.4) !important;
            color: #ffffff !important;
            box-shadow: 0 0 15px rgba(239, 35, 60, 0.15) !important;
        }

        /* Expanders (Day Topic Cards) */
        div[data-testid="stExpander"] {
            background: rgba(14, 14, 18, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            margin-bottom: 12px !important;
            transition: all 0.25s ease !important;
        }
        div[data-testid="stExpander"]:hover {
            border-color: rgba(239, 35, 60, 0.35) !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
        }

        /* Progress Bar */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #ef233c 0%, #ff4d6d 100%) !important;
            box-shadow: 0 0 16px rgba(239, 35, 60, 0.6) !important;
            border-radius: 9999px !important;
        }
        .stProgress > div > div > div {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 9999px !important;
        }

        /* Callout Notifications */
        div[data-testid="stNotification"], div[data-testid="stAlert"] {
            background: rgba(18, 18, 22, 0.85) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-left: 3px solid #ef233c !important;
            border-radius: 10px !important;
            color: #e4e4e7 !important;
        }

        /* Links */
        a {
            color: #ff4d6d !important;
            text-decoration: none !important;
            transition: color 0.2s ease !important;
        }
        a:hover {
            color: #ef233c !important;
            text-decoration: underline !important;
            text-shadow: 0 0 8px rgba(239, 35, 60, 0.4) !important;
        }

        /* Studio & Workspace Containers */
        .studio-card {
            background: rgba(14, 14, 18, 0.7);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 20px 22px;
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
        }
        .studio-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #ef233c, transparent);
        }
        .studio-badge {
            font-family: 'Manrope', sans-serif;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #ef233c;
            margin-bottom: 4px;
        }
        .studio-title {
            font-family: 'Manrope', sans-serif;
            font-size: 1.25rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.02em;
            margin-bottom: 4px;
        }
        .studio-desc {
            font-size: 0.85rem;
            color: #a1a1aa;
            line-height: 1.45;
        }
        .workspace-empty-card {
            background: rgba(14, 14, 18, 0.6);
            backdrop-filter: blur(20px);
            border: 1px dashed rgba(255, 255, 255, 0.12);
            border-radius: 18px;
            padding: 40px 28px;
            text-align: center;
        }
        .workspace-feature-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 24px;
            text-align: left;
        }
        .workspace-feature-item {
            background: rgba(22, 22, 28, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 16px;
            transition: all 0.25s ease;
        }
        .workspace-feature-item:hover {
            border-color: rgba(239, 35, 60, 0.3);
            transform: translateY(-2px);
        }
        .workspace-feature-title {
            font-family: 'Manrope', sans-serif;
            font-size: 0.92rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }
        .workspace-feature-desc {
            font-size: 0.78rem;
            color: #a1a1aa;
            line-height: 1.4;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize Session State
    if "roadmap" not in st.session_state:
        st.session_state.roadmap = None
    if "completion_state" not in st.session_state:
        st.session_state.completion_state = {}
    if "last_progress_msg" not in st.session_state:
        st.session_state.last_progress_msg = ""
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    if "goal_preset" not in st.session_state:
        st.session_state.goal_preset = "Master Python for Data Science and Machine Learning"
    if "skill_preset" not in st.session_state:
        st.session_state.skill_preset = "Beginner"
    if "duration_val_preset" not in st.session_state:
        st.session_state.duration_val_preset = 14
    if "duration_unit_preset" not in st.session_state:
        st.session_state.duration_unit_preset = "Days"
    if "daily_time_val_preset" not in st.session_state:
        st.session_state.daily_time_val_preset = 2.0
    if "format_preset" not in st.session_state:
        st.session_state.format_preset = "Mixed"

    # Sidebar Configuration
    st.sidebar.markdown('### <span class="brand-diamond"></span> Control Center', unsafe_allow_html=True)

    # API Key & Model Configuration
    with st.sidebar.expander("Model Settings", expanded=True):
        default_api_key = AppConfig.get_gemini_api_key() or ""
        api_key_input = st.text_input(
            "Gemini API Key",
            value=default_api_key,
            type="password",
            help="Get a free key at https://aistudio.google.com/"
        )
        
        selected_model = st.selectbox(
            "Model Version",
            ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
            index=0,
            help="Recommended: gemini-2.5-flash for fast and structured reasoning"
        )

    # MCP Server Endpoints (Pipedream)
    with st.sidebar.expander("MCP Integrations (Pipedream)", expanded=True):
        st.markdown("""
        External tool orchestration via **Model Context Protocol (MCP)** streamable HTTP servers.
        """)
        
        default_yt_url = AppConfig.get_youtube_mcp_url() or ""
        yt_mcp_url = st.text_input(
            "YouTube MCP Server URL",
            value=default_yt_url,
            placeholder="https://...pipedream.net/mcp",
            help="Used to discover and verify educational video tutorials via YouTube Data MCP."
        )
        if st.button("Test YouTube MCP", key="test_yt_btn"):
            if yt_mcp_url:
                with st.spinner("Testing YouTube MCP server connection..."):
                    res = MCPManager.test_server_connection_sync("youtube", yt_mcp_url)
                    if res["status"] == "connected":
                        st.success(res["message"])
                        st.caption(f"Discovered Tools: {', '.join(res['tools'])}")
                    else:
                        st.error(res["message"])
            else:
                st.warning("Please enter a YouTube MCP endpoint URL to test.")

        default_drive_url = AppConfig.get_drive_mcp_url() or ""
        drive_mcp_url = st.text_input(
            "Google Drive MCP Server URL",
            value=default_drive_url,
            placeholder="https://...pipedream.net/mcp",
            help="Used to export and save generated roadmaps directly to Google Drive."
        )
        if st.button("Test Google Drive MCP", key="test_drive_btn"):
            if drive_mcp_url:
                with st.spinner("Testing Google Drive MCP server connection..."):
                    res = MCPManager.test_server_connection_sync("drive", drive_mcp_url)
                    if res["status"] == "connected":
                        st.success(res["message"])
                        st.caption(f"Discovered Tools: {', '.join(res['tools'])}")
                    else:
                        st.error(res["message"])
            else:
                st.warning("Please enter a Google Drive MCP endpoint URL to test.")

        default_notion_url = AppConfig.get_notion_mcp_url() or ""
        notion_mcp_url = st.text_input(
            "Notion MCP Server URL (Optional)",
            value=default_notion_url,
            placeholder="https://...pipedream.net/mcp",
            help="Optional secondary tool for exporting to Notion workspace."
        )

    # Sidebar MCP Status Indicator
    has_mcp = bool(yt_mcp_url.strip() or drive_mcp_url.strip() or notion_mcp_url.strip())
    if has_mcp:
        st.sidebar.markdown("""
        <div style="margin-top: 15px;">
            <div class="badge-pill">
                <span class="pulse-dot-container"><span class="pulse-ping"></span><span class="pulse-solid"></span></span>
                MCP Connected
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div style="margin-top: 15px;">
            <div class="badge-pill" style="border-color: rgba(255,255,255,0.06); color: #71717a;">
                ○ Standard Mode
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Main Dashboard Header
    col_header, col_status = st.columns([4, 1])
    with col_header:
        st.markdown("""
        <div>
            <div class="main-title"><span class="brand-diamond"></span>Learning Path <span class="accent-red">Generator</span></div>
            <div class="sub-title">Generate personalized, day-by-day learning roadmaps customized to your schedule and goals.</div>
        </div>
        """, unsafe_allow_html=True)

    with col_status:
        if has_mcp:
            st.markdown("""
            <div style="text-align: right; padding-top: 25px;">
                <div class="badge-pill" style="border-color: rgba(239, 35, 60, 0.4); box-shadow: 0 0 15px rgba(239, 35, 60, 0.2);">
                    <span class="pulse-dot-container"><span class="pulse-ping"></span><span class="pulse-solid"></span></span>
                    MCP Active
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: right; padding-top: 25px;">
                <div class="badge-pill" style="border-color: rgba(255,255,255,0.1);">
                    Standalone
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Two-Column Studio Layout
    col_studio, col_workspace = st.columns([1, 1.45], gap="large")

    with col_studio:
        st.markdown("""
        <div class="studio-card">
            <div class="studio-badge">Roadmap Studio</div>
            <div class="studio-title">Configure Your Goal</div>
            <div class="studio-desc">Define your target subject or pick a quick-start preset below to build your custom schedule.</div>
        </div>
        """, unsafe_allow_html=True)

        st.caption("Quick-Start Presets")
        pr_col1, pr_col2 = st.columns(2)
        with pr_col1:
            if st.button("Python for Data Science", key="btn_p1", use_container_width=True):
                st.session_state.goal_preset = "Master Python for Data Science and Machine Learning"
                st.session_state.skill_preset = "Beginner"
                st.session_state.duration_val_preset = 14
                st.session_state.duration_unit_preset = "Days"
                st.session_state.daily_time_val_preset = 2.0
                st.session_state.format_preset = "Mixed"
                st.rerun()
            if st.button("System Design", key="btn_p2", use_container_width=True):
                st.session_state.goal_preset = "System Design & Distributed Architecture for Senior Engineers"
                st.session_state.skill_preset = "Advanced"
                st.session_state.duration_val_preset = 10
                st.session_state.duration_unit_preset = "Days"
                st.session_state.daily_time_val_preset = 2.5
                st.session_state.format_preset = "Documentation"
                st.rerun()
        with pr_col2:
            if st.button("Full-Stack React & Node", key="btn_p3", use_container_width=True):
                st.session_state.goal_preset = "Full-Stack Web Development with React, TypeScript, and Node.js"
                st.session_state.skill_preset = "Intermediate"
                st.session_state.duration_val_preset = 21
                st.session_state.duration_unit_preset = "Days"
                st.session_state.daily_time_val_preset = 3.0
                st.session_state.format_preset = "Projects"
                st.rerun()
            if st.button("DevOps & Kubernetes", key="btn_p4", use_container_width=True):
                st.session_state.goal_preset = "DevOps, Docker, CI/CD Pipelines, and Kubernetes Deployment"
                st.session_state.skill_preset = "Intermediate"
                st.session_state.duration_val_preset = 14
                st.session_state.duration_unit_preset = "Days"
                st.session_state.daily_time_val_preset = 2.0
                st.session_state.format_preset = "Exercises"
                st.rerun()

        # Input Form
        with st.form("learning_path_form"):
            st.subheader("Step 1: Target Goal")
            goal_input = st.text_input(
                "What do you want to learn?",
                value=st.session_state.goal_preset,
                placeholder="e.g. Master Java Programming for Backend Development",
                help="Specify the subject or technology you want to master."
            )

            st.subheader("Step 2: Profile & Schedule")
            
            c_skill, c_dur = st.columns(2)
            with c_skill:
                skill_index = ["Beginner", "Intermediate", "Advanced"].index(st.session_state.skill_preset) if st.session_state.skill_preset in ["Beginner", "Intermediate", "Advanced"] else 0
                skill_level = st.selectbox(
                    "Current Skill Level",
                    ["Beginner", "Intermediate", "Advanced"],
                    index=skill_index
                )
            with c_dur:
                duration_val = st.number_input(
                    "Total Duration",
                    min_value=1,
                    max_value=90,
                    value=int(st.session_state.duration_val_preset),
                    step=1
                )

            c_dur_unit, c_daily = st.columns(2)
            with c_dur_unit:
                unit_index = ["Days", "Weeks"].index(st.session_state.duration_unit_preset) if st.session_state.duration_unit_preset in ["Days", "Weeks"] else 0
                duration_unit = st.selectbox("Duration Unit", ["Days", "Weeks"], index=unit_index)
            with c_daily:
                daily_time_val = st.number_input(
                    "Daily Commitment",
                    min_value=0.5,
                    max_value=12.0,
                    value=float(st.session_state.daily_time_val_preset),
                    step=0.5
                )

            c_fmt, c_time_unit = st.columns(2)
            with c_fmt:
                format_options = ["Mixed", "Videos", "Documentation", "Exercises", "Projects"]
                fmt_idx = format_options.index(st.session_state.format_preset) if st.session_state.format_preset in format_options else 0
                pref_format = st.selectbox("Preferred Format", format_options, index=fmt_idx)
            with c_time_unit:
                daily_time_unit = st.selectbox("Time Unit", ["Hours", "Minutes"], index=0)

            # Optional Customization
            with st.expander("Advanced Customization (Optional)"):
                known_topics = st.text_input(
                    "Topics you already know (to skip)",
                    placeholder="e.g. Basic syntax, variables, if-else statements"
                )
                learning_pref = st.text_input(
                    "Specific preferences or constraints",
                    placeholder="e.g. Focus on practical projects, explain with visual diagrams"
                )
                final_objective = st.text_input(
                    "Target Objective",
                    placeholder="e.g. Pass technical interview, build full-stack portfolio app, college exam"
                )

            submit_button = st.form_submit_button("Generate Learning Roadmap", type="primary", use_container_width=True)

        with st.expander("How It Works & Architecture Overview", expanded=False):
            st.markdown("""
            1. **Personalized Roadmaps**: Enter your subject, available days, and daily study hours. The curriculum calibrates every day's workload to fit your schedule.
            2. **Model Context Protocol (MCP)**:
               - **YouTube MCP Server**: Discovers genuine educational video resources and validates playlist recommendations.
               - **Google Drive MCP Server**: Directly creates and uploads your roadmap document to your connected cloud storage.
            3. **Interactive Tracking**: Check off daily modules as you learn. Progress is calculated and maintained in real-time.
            4. **Offline / Standalone Fallback**: If MCP servers are not yet connected, the application seamlessly creates curated search-linked paths and provides instant Markdown & JSON downloads.
            """)

    with col_workspace:
        # Generation Logic status indicators
        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        if submit_button:
            if not api_key_input:
                st.error("Gemini API Key is required. Please enter your API key in the sidebar or set GEMINI_API_KEY in your .env file.")
            elif not goal_input or len(goal_input.strip()) < 3:
                st.warning("Please enter a clear learning goal (at least 3 characters).")
            else:
                try:
                    student_data = StudentGoalInput(
                        goal=goal_input.strip(),
                        skill_level=skill_level,
                        duration_value=int(duration_val),
                        duration_unit=duration_unit,
                        daily_time_value=float(daily_time_val),
                        daily_time_unit=daily_time_unit,
                        learning_format=pref_format,
                        prior_knowledge=known_topics.strip() if known_topics else None,
                        learning_preferences=learning_pref.strip() if learning_pref else None,
                        final_objective=final_objective.strip() if final_objective else None
                    )

                    progress_bar = progress_placeholder.progress(0.0)

                    def update_progress_ui(msg: str, progress: float):
                        progress_bar.progress(progress)
                        status_placeholder.info(msg)

                    generator = AILearningPathGenerator(
                        api_key=api_key_input,
                        model_name=selected_model
                    )

                    with st.spinner("Generating your structured roadmap..."):
                        generated_roadmap = generator.generate_roadmap(
                            student_input=student_data,
                            progress_callback=update_progress_ui,
                            youtube_url=yt_mcp_url,
                            drive_url=drive_mcp_url,
                            notion_url=notion_mcp_url
                        )

                    st.session_state.roadmap = generated_roadmap
                    st.session_state.completion_state = {day.day_number: False for day in generated_roadmap.days}
                    status_placeholder.success("Learning path successfully generated!")
                    progress_placeholder.empty()
                    st.rerun()

                except Exception as e:
                    st.error(f"Error during generation: {str(e)}")
                    st.info("Tip: Verify your Gemini API key in the sidebar and ensure you have internet access.")

        # Workspace Content (Empty State vs Active Roadmap)
        if not st.session_state.roadmap:
            st.markdown("""
            <div class="workspace-empty-card">
                <div style="font-family: 'Manrope', sans-serif; font-size: 1.45rem; font-weight: 800; color: #ffffff; margin-bottom: 8px;">
                    Curriculum Workspace
                </div>
                <div style="font-size: 0.92rem; color: #a1a1aa; max-width: 520px; margin: 0 auto 20px auto; line-height: 1.6;">
                    Select a quick-start preset or enter your custom goal in the studio on the left. Your dynamic day-by-day learning roadmap, verified tutorials, and project milestones will render here.
                </div>
                <div class="workspace-feature-grid">
                    <div class="workspace-feature-item">
                        <div class="workspace-feature-title">Day-by-Day Progression</div>
                        <div class="workspace-feature-desc">Calibrated daily workloads with concept explanations, key takeaways, and daily assignments.</div>
                    </div>
                    <div class="workspace-feature-item">
                        <div class="workspace-feature-title">Live Tool Intelligence</div>
                        <div class="workspace-feature-desc">Automated video discovery via YouTube MCP with direct verification badges.</div>
                    </div>
                    <div class="workspace-feature-item">
                        <div class="workspace-feature-title">Capstone & Cloud Sync</div>
                        <div class="workspace-feature-desc">Full project rubric, next steps, and 1-click Google Drive or Markdown export.</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            roadmap: LearningRoadmap = st.session_state.roadmap
            
            for day in roadmap.days:
                day.completed = st.session_state.completion_state.get(day.day_number, False)

            # Roadmap Overview Banner
            st.markdown(f"""
            <div style="background: rgba(18, 18, 22, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 18px 22px; margin-bottom: 16px;">
                <div style="font-family: 'Manrope', sans-serif; font-size: 1.35rem; font-weight: 800; color: #ffffff; margin-bottom: 4px;">{roadmap.title}</div>
                <div style="font-size: 0.88rem; color: #a1a1aa;"><strong>Goal:</strong> {roadmap.goal} &nbsp;|&nbsp; <strong>Skill Level:</strong> <code style="color: #ef233c;">{roadmap.skill_level}</code></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics Row in Red Noir Dark Cards
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{roadmap.total_duration}</div>
                    <div class="metric-label">Total Duration</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{roadmap.daily_commitment}</div>
                    <div class="metric-label">Daily Study Time</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{roadmap.completed_count} / {roadmap.total_days_count}</div>
                    <div class="metric-label">Days Completed</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{roadmap.progress_percentage}%</div>
                    <div class="metric-label">Total Progress</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.progress(roadmap.progress_percentage / 100.0)

            # Quick Action Controls
            col_ctrl1, col_ctrl2 = st.columns([1, 4])
            with col_ctrl1:
                if st.button("Mark All Complete", use_container_width=True):
                    for d in roadmap.days:
                        st.session_state.completion_state[d.day_number] = True
                    st.rerun()
            with col_ctrl2:
                if st.button("Reset Progress"):
                    for d in roadmap.days:
                        st.session_state.completion_state[d.day_number] = False
                    st.rerun()

            # Expected Outcome & Milestones
            col_out, col_ms = st.columns([1, 1])
            with col_out:
                st.markdown("### Expected Outcome")
                st.info(roadmap.expected_outcome)
            with col_ms:
                st.markdown("### Key Milestones")
                if roadmap.milestones:
                    for i, ms in enumerate(roadmap.milestones, 1):
                        st.markdown(f"**{i}.** {ms}")
                else:
                    st.write("Complete each daily module to advance towards the capstone project.")

            # Day-by-Day Modules
            st.markdown("### Day-by-Day Learning Curriculum")
            
            for day in roadmap.days:
                completion_suffix = " (Completed)" if day.completed else ""
                expander_title = f"Day {day.day_number}: {day.topic_title} — ({day.estimated_time}){completion_suffix}"
                
                with st.expander(expander_title, expanded=(not day.completed)):
                    col_check, col_details = st.columns([1, 6])
                    with col_check:
                        is_done = st.checkbox(
                            "Completed",
                            value=st.session_state.completion_state.get(day.day_number, False),
                            key=f"check_day_{day.day_number}"
                        )
                        if is_done != st.session_state.completion_state.get(day.day_number, False):
                            st.session_state.completion_state[day.day_number] = is_done
                            st.rerun()

                    with col_details:
                        st.markdown("#### Concept Explanation")
                        st.write(day.concept_explanation)

                        if day.key_takeaways:
                            st.markdown("**Key Takeaways:**")
                            for k in day.key_takeaways:
                                st.markdown(f"- {k}")

                        if day.resources:
                            st.markdown("#### Recommended Learning Resources")
                            for res in day.resources:
                                badge = " `[Verified via Pipedream YouTube MCP]`" if res.is_mcp_verified else ""
                                author_info = f" by *{res.channel_or_author}*" if res.channel_or_author else ""
                                st.markdown(f"**[{res.title}]({res.url})** ({res.platform}){author_info}{badge}")
                                if res.relevance_note:
                                    st.caption(f"Relevance: {res.relevance_note}")

                        if day.practice_exercises:
                            st.markdown("#### Hands-on Practice Exercises")
                            for ex in day.practice_exercises:
                                st.markdown(f"- {ex}")

                        if day.assignment:
                            st.markdown("#### Daily Assignment")
                            st.info(day.assignment)

                        if day.revision_checkpoint:
                            st.markdown("#### Revision Checkpoint")
                            st.caption(f"Self Check: {day.revision_checkpoint}")

            # Capstone Project
            if roadmap.capstone_project:
                st.markdown("---")
                st.markdown("### Final Practical Capstone Project")
                st.success(f"**{roadmap.capstone_project.title}**\n\n{roadmap.capstone_project.description}")
                if roadmap.capstone_project.deliverables:
                    st.markdown("**Deliverables & Evaluation Criteria:**")
                    for d in roadmap.capstone_project.deliverables:
                        st.markdown(f"- {d}")

            # Next Steps
            if roadmap.next_steps:
                st.markdown("### Next Steps & Further Learning")
                for step in roadmap.next_steps:
                    st.markdown(f"- {step}")

            # Export & Cloud Storage Section
            st.markdown("---")
            st.subheader("Export & Cloud Sharing")
            
            col_dl1, col_dl2, col_drive = st.columns(3)
            
            with col_dl1:
                md_text = RoadmapExporter.to_markdown(roadmap)
                st.download_button(
                    label="Download Markdown (.md)",
                    data=md_text,
                    file_name=f"{roadmap.title.replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            with col_dl2:
                json_text = RoadmapExporter.to_json(roadmap)
                st.download_button(
                    label="Download JSON (.json)",
                    data=json_text,
                    file_name=f"{roadmap.title.replace(' ', '_')}.json",
                    mime="application/json",
                    use_container_width=True
                )

            with col_drive:
                if st.button("Save to Google Drive (MCP)", use_container_width=True):
                    if drive_mcp_url and drive_mcp_url.strip():
                        with st.spinner("Connecting to Pipedream Google Drive MCP server and saving..."):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                save_res = loop.run_until_complete(
                                    RoadmapExporter.save_to_google_drive_mcp(roadmap, drive_mcp_url.strip())
                                )
                                if save_res.get("success"):
                                    st.success(save_res['message'])
                                else:
                                    st.error(save_res['message'])
                            finally:
                                loop.close()
                    else:
                        st.warning("Google Drive MCP URL is not configured. Please enter your Pipedream Drive MCP URL in the sidebar to save directly to the cloud.")




if __name__ == "__main__":
    main()
