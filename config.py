"""
Configuration and environment settings.

All secrets come from the environment (.env) or from the sidebar at runtime.
Nothing is hardcoded.
"""

from __future__ import annotations

import os
from pathlib import Path
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


class AppConfig:
    """Reads configuration from environment variables with explicit overrides."""

    @staticmethod
    def _first_env(*names: str) -> Optional[str]:
        for name in names:
            value = os.getenv(name)
            if value and value.strip():
                return value.strip()
        return None

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
