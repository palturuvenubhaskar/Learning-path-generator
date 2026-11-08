"""Tests for saving sidebar settings to .env."""

from __future__ import annotations

import os

import config
from config import AppConfig


def _use_temp_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    return env_file


def test_save_creates_env_file(tmp_path, monkeypatch):
    env_file = _use_temp_env(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "old")

    AppConfig.save_env_value("OPENROUTER_API_KEY", "sk-or-v1-new")

    assert env_file.read_text(encoding="utf-8") == "OPENROUTER_API_KEY=sk-or-v1-new\n"
    assert os.environ["OPENROUTER_API_KEY"] == "sk-or-v1-new"
    assert AppConfig.get_openrouter_api_key() == "sk-or-v1-new"


def test_save_replaces_one_value_and_keeps_comments(tmp_path, monkeypatch):
    env_file = _use_temp_env(tmp_path, monkeypatch)
    env_file.write_text(
        "# keep this comment\nOPENROUTER_API_KEY=old\nOPENROUTER_MODEL=already\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "old")

    AppConfig.save_env_value("OPENROUTER_API_KEY", "new")

    assert env_file.read_text(encoding="utf-8") == (
        "# keep this comment\nOPENROUTER_API_KEY=new\nOPENROUTER_MODEL=already\n"
    )


def test_save_appends_missing_key(tmp_path, monkeypatch):
    env_file = _use_temp_env(tmp_path, monkeypatch)
    env_file.write_text("OTHER=1", encoding="utf-8")
    monkeypatch.setenv("OPENROUTER_MODEL", "")

    AppConfig.save_env_value("OPENROUTER_MODEL", "vendor/model:free")

    assert env_file.read_text(encoding="utf-8") == "OTHER=1\nOPENROUTER_MODEL=vendor/model:free\n"


def test_save_quotes_values_with_spaces(tmp_path, monkeypatch):
    env_file = _use_temp_env(tmp_path, monkeypatch)
    monkeypatch.setenv("PIPEDREAM_YOUTUBE_MCP_URL", "")

    AppConfig.save_env_value("PIPEDREAM_YOUTUBE_MCP_URL", "https://example.com/a b")

    assert 'PIPEDREAM_YOUTUBE_MCP_URL="https://example.com/a b"' in env_file.read_text(
        encoding="utf-8"
    )


def test_clearing_a_value_blanks_it(tmp_path, monkeypatch):
    env_file = _use_temp_env(tmp_path, monkeypatch)
    env_file.write_text("OPENROUTER_API_KEY=old\n", encoding="utf-8")
    monkeypatch.setenv("OPENROUTER_API_KEY", "old")

    AppConfig.save_env_value("OPENROUTER_API_KEY", "")

    assert env_file.read_text(encoding="utf-8") == "OPENROUTER_API_KEY=\n"
    assert AppConfig.get_openrouter_api_key() is None
