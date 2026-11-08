"""
Configuration and environment settings.

All secrets come from the environment (.env) or from the sidebar at runtime.
Nothing is hardcoded.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from threading import Lock
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# OpenRouter is OpenAI-compatible, so the plain `openai` SDK talks to it.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Hard product limit. Long plans produce truncated JSON on free models.
MAX_PLAN_DAYS = 30

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("LPG_DATA_DIR") or (PROJECT_ROOT / "data"))
ENV_FILE = PROJECT_ROOT / ".env"
_ENV_WRITE_LOCK = Lock()


def _dotenv_value(value: str) -> str:
    """Quote only values that would otherwise confuse dotenv."""
    if not value:
        return ""
    if any(char.isspace() for char in value) or "#" in value or '"' in value:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


class AppConfig:
    """Reads configuration from environment variables with explicit overrides."""

    @staticmethod
    def _first_env(*names: str) -> Optional[str]:
        for name in names:
            value = os.getenv(name)
            if value and value.strip():
                return value.strip()
        return None

    @staticmethod
    def save_env_value(name: str, value: str) -> None:
        """Persist one variable in .env, keeping comments and other settings.

        The runtime environment is updated too, so the current session sees the
        change without a restart.
        """
        cleaned = (value or "").strip()
        assignment = f"{name}={_dotenv_value(cleaned)}"
        pattern = re.compile(rf"^[ \t]*{re.escape(name)}[ \t]*=.*$", re.MULTILINE)
        with _ENV_WRITE_LOCK:
            text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
            if pattern.search(text):
                text = pattern.sub(assignment, text, count=1)
            else:
                if text and not text.endswith("\n"):
                    text += "\n"
                text += assignment + "\n"
            ENV_FILE.write_text(text, encoding="utf-8")
        os.environ[name] = cleaned

    @classmethod
    def get_openrouter_api_key(cls, override: Optional[str] = None) -> Optional[str]:
        """API key from the sidebar override, then .env."""
        if override and override.strip():
            return override.strip()
        return cls._first_env("OPENROUTER_API_KEY")

    @classmethod
    def get_default_model(cls, override: Optional[str] = None) -> Optional[str]:
        """Preferred model id from the sidebar override, then .env."""
        if override and override.strip():
            return override.strip()
        return cls._first_env("OPENROUTER_MODEL")

    @classmethod
    def get_youtube_mcp_url(cls, override: Optional[str] = None) -> Optional[str]:
        if override and override.strip():
            return override.strip()
        return cls._first_env("PIPEDREAM_YOUTUBE_MCP_URL")

    @classmethod
    def get_drive_mcp_url(cls, override: Optional[str] = None) -> Optional[str]:
        if override and override.strip():
            return override.strip()
        return cls._first_env("PIPEDREAM_DRIVE_MCP_URL")

    @classmethod
    def get_notion_mcp_url(cls, override: Optional[str] = None) -> Optional[str]:
        if override and override.strip():
            return override.strip()
        return cls._first_env("PIPEDREAM_NOTION_MCP_URL")

    @classmethod
    def get_data_dir(cls) -> Path:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return DATA_DIR
