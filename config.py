"""
Configuration and Environment Settings for the AI Learning Path Generator.
Loads environment variables from .env if present.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file from workspace root if present
load_dotenv()


class AppConfig:
    """Application configuration and credentials loader."""
    
    @staticmethod
    def get_gemini_api_key(override: Optional[str] = None) -> Optional[str]:
        """Returns API key from parameter override, .env, or environment."""
        if override and override.strip():
            return override.strip()
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    @staticmethod
    def get_gemini_model(override: Optional[str] = None) -> str:
        """Returns Gemini model identifier."""
        if override and override.strip():
            return override.strip()
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @staticmethod
    def get_youtube_mcp_url(override: Optional[str] = None) -> Optional[str]:
        """Returns Pipedream YouTube MCP URL."""
        if override and override.strip():
            return override.strip()
        return os.getenv("PIPEDREAM_YOUTUBE_MCP_URL")

    @staticmethod
    def get_drive_mcp_url(override: Optional[str] = None) -> Optional[str]:
        """Returns Pipedream Google Drive MCP URL."""
        if override and override.strip():
            return override.strip()
        return os.getenv("PIPEDREAM_DRIVE_MCP_URL")

    @staticmethod
    def get_notion_mcp_url(override: Optional[str] = None) -> Optional[str]:
        """Returns Pipedream Notion MCP URL."""
        if override and override.strip():
            return override.strip()
        return os.getenv("PIPEDREAM_NOTION_MCP_URL")
