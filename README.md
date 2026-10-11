# 📘 AI Learning Path Generator 🎓
### *Model Context Protocol (MCP) Project*

An intelligent, interactive learning path generator that builds personalized, day-by-day educational roadmaps using **Google Gemini** models and the **Model Context Protocol (MCP)** via Pipedream for real-time external tool orchestration (YouTube, Google Drive, Notion).

---

## 🌟 Executive Summary & Workshop Evaluation Guide

### 1. The Problem Being Solved
Students and self-learners often struggle with self-directed learning because generic course curricula do not adapt to their personal constraints. A student with 15 days and 2 hours per day receives the same static syllabus as a full-time student, leading to cognitive overload, dropped courses, and lack of real practical project completion.

### 2. The Solution
The **AI Learning Path Generator** analyzes the student's unique goal, starting level, total duration, and exact daily commitment. It crafts a custom, time-calibrated day-by-day curriculum complete with conceptual explanations, curated video resources, hands-on exercises, daily assignments, revision checkpoints, and a capstone project.

### 3. How AI is Used
- **Curriculum Architecture**: Powered by Google Gemini (`gemini-2.5-flash`), structuring pedagogical progressions from first principles to advanced implementations.
- **Time Calibration**: Calibrates each day's study workload to fit the user's explicit daily study hours.
- **Structured Output**: Enforces strict Pydantic JSON schemas, converting LLM reasoning into interactive, manageable UI components.

### 4. What MCP Contributes
The **Model Context Protocol (MCP)** connects the AI agent directly to external tools and ecosystems:
- **YouTube Data MCP Server (Pipedream)**: Discovers and verifies real educational tutorials and video resources.
- **Google Drive MCP Server (Pipedream)**: Enables cloud persistence by allowing the student to save the generated roadmap directly to their Google Drive with one click.
- **Notion MCP Server (Pipedream)**: Connects to workspace pages for structured note-taking.
- **Dynamic Introspection**: Discovers available tools dynamically via streamable HTTP / SSE transports without hardcoded endpoints.

### 5. 2-3 Minute Live Demonstration Script
1. **Launch**: Run `streamlit run app.py` and open `http://localhost:8501`.
2. **Configuration**: Show the sidebar. Enter or confirm the Gemini API Key. Click **"Test YouTube MCP"** or **"Test Google Drive MCP"** to demonstrate live MCP tool inspection.
3. **Input Goal**: Enter `"Learn Java programming in 15 days"`, select `Beginner`, `15 Days`, `2.0 Hours/Day`, `Mixed` format.
4. **Generate**: Click **"Generate My Learning Roadmap"**. Watch the step-by-step progress indicator.
5. **Interactive Exploration**:
   - Inspect Day 1: expand the card, review the concept explanation, key takeaways, and recommended resources with `[MCP Verified]` badges.
   - Click the **"Completed"** checkbox on Day 1: watch the overall progress bar update from `0%` to `6.7%` in real-time.
   - Highlight the **Final Capstone Project** and **Next Steps** at the bottom.
6. **Export**: Click **"Download Markdown (.md)"** or **"Download JSON (.json)"**, or click **"Save to Google Drive (MCP)"** to demonstrate cloud export.

---

## 🏗️ Project Architecture & Structure

```
v:\PROJECTS\LEARNING PATH GENERATOR\
├── app.py                     # Primary Streamlit application entry point
├── dashboard.py               # Interactive UI components & state management
├── config.py                  # Environment variables & configuration loader
├── models.py                  # Pydantic data schemas for inputs & roadmaps
├── mcp_client.py              # Pipedream MCP connection manager & tool discovery
├── ai_generator.py            # Gemini AI generation & structured JSON parser
├── exporter.py                # Markdown, JSON, and Google Drive MCP exports
├── conftest.py                # Pytest configuration & sys.path setup
├── requirements.txt           # Verified Python dependencies
├── .env.example              # Sample environment configuration file
├── .gitignore                 # Git ignore rules for virtual environments & secrets
├── tests/                     # Automated test suite (15 passing tests)
│   ├── test_models.py         # Input validation & progress calculation tests
│   ├── test_ai_generator.py   # JSON extraction & LLM pipeline tests
│   ├── test_mcp_client.py     # MCP config & connection health tests
│   └── test_exporter.py       # Markdown, JSON & Drive export tests
└── Learning-Path-Generator/   # Backward-compatible subfolder entry point
    ├── app.py                 # Subfolder runner (bridges to root)
    ├── utils.py               # Enhanced LangGraph MCP runner
    ├── prompt.py              # Legacy prompt template
    └── requirements.txt       # Dependencies
```

---

## 🛠️ Prerequisites

- **Operating System**: Windows 10/11 (or macOS / Linux)
- **Python**: Version 3.10, 3.11, or 3.12 (Tested on Python 3.12.10)
- **Google Gemini API Key**: Free API key from [Google AI Studio](https://aistudio.google.com/)
- **Pipedream Account (Optional for MCP)**: [Pipedream MCP](https://mcp.pipedream.com/) for YouTube & Drive tools

---

## 💻 Installation & Setup (Windows)

### Step 1: Open Terminal in Project Directory
Open PowerShell or Command Prompt in the project folder:
```powershell
cd "v:\PROJECTS\LEARNING PATH GENERATOR"
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create virtual environment named venv
python -m venv venv

# Activate on Windows PowerShell:
.\venv\Scripts\Activate.ps1

# (If using Windows Command Prompt cmd.exe instead):
# venv\Scripts\activate.bat
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Open `.env` and fill in your Gemini API Key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
PIPEDREAM_YOUTUBE_MCP_URL=
PIPEDREAM_DRIVE_MCP_URL=
PIPEDREAM_NOTION_MCP_URL=
```
*(Note: You can also enter or paste your API key directly in the Streamlit web sidebar).*

---

## 🚀 Running the Application

Start the Streamlit dashboard:
```powershell
streamlit run app.py
```

The application will open automatically in your browser at:
**[http://localhost:8501](http://localhost:8501)**

*(Alternatively, running `streamlit run Learning-Path-Generator/app.py` also works seamlessly).*

---

## 🔌 Setting Up Pipedream MCP Servers

### How Pipedream MCP Works
Pipedream hosts streamable HTTP / SSE MCP servers that expose authenticated API actions (like searching YouTube or writing files to Google Drive) to LLMs via standard JSON-RPC.

1. Sign up or log in at [pipedream.com](https://pipedream.com/).
2. Navigate to the **MCP** section or [mcp.pipedream.com](https://mcp.pipedream.com/).
3. **YouTube MCP**:
   - Create a YouTube Data MCP Server.
   - Authorize your Google/YouTube account.
   - Copy the streamable HTTP endpoint URL (e.g. `https://...pipedream.net/mcp`).
   - Paste it into the app sidebar under **YouTube MCP Server URL**.
   - Click **"🔍 Test YouTube MCP"** to inspect discovered tools (e.g. `youtube_search`).
4. **Google Drive MCP**:
   - Create a Google Drive MCP Server.
   - Authorize Google Drive access.
   - Copy the endpoint URL and paste into **Google Drive MCP Server URL**.
   - Click **"🔍 Test Google Drive MCP"** to verify connection.

### Standalone / Fallback Mode
If you do not have Pipedream MCP servers set up, the application runs seamlessly in **Native AI Mode**:
- Generates comprehensive, time-calibrated roadmaps.
- Provides search-linked YouTube recommendations.
- Offers instant Markdown (`.md`) and JSON (`.json`) downloads.

---

## 🧪 Automated Testing

Run the automated test suite with pytest:
```powershell
python -m pytest -v
```

### Test Coverage Summary:
- `tests/test_models.py`: Validates input constraints, day/week conversions, daily time limits, and real-time progress calculations.
- `tests/test_ai_generator.py`: Validates JSON extraction from LLM markdown fences and pipeline mocking.
- `tests/test_mcp_client.py`: Validates MCP configuration generation, unconfigured server handling, and timeout resilience.
- `tests/test_exporter.py`: Validates Markdown rendering, JSON serialization, and Google Drive upload error handling.

**Result**: 15 / 15 tests passing.

---

## 🛡️ Security Best Practices
- **No Hardcoded Keys**: API keys and tokens are loaded strictly via `.env` or temporary session UI inputs.
- **Git Protection**: `.env`, `venv/`, and cache directories are excluded via `.gitignore`.
- **Zero Token Leakage**: Credentials are masked with password inputs and never written to logs or outputs.

---

## ❓ Troubleshooting & FAQs

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Gemini API Key is required` | No key in `.env` or sidebar | Enter key at `https://aistudio.google.com/` and paste into the sidebar. |
| `Connection timed out` on MCP test | Unreachable Pipedream endpoint | Check if your Pipedream workflow is active and permissions are granted. |
| `Port 8501 is already in use` | Another Streamlit instance running | Run `streamlit run app.py --server.port 8502`. |
| Script execution policy error in PowerShell | PowerShell execution policy restricted | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`. |

## 👤 Author & Maintainer
- **Palturu Venu Bhaskar** — [@palturuvenubhaskar](https://github.com/palturuvenubhaskar)
- Repository: [Learning-path-generator](https://github.com/palturuvenubhaskar/Learning-path-generator)

---

## 📄 License & Credits
Built with **Google Gemini & Model Context Protocol (MCP)**.  
Licensed under the [MIT License](LICENSE).
