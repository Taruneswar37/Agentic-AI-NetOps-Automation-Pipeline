"""
Tests for src.config — Settings loader.
"""

import os
import pytest


def test_settings_loads_defaults():
    """Settings should load with defaults when no .env exists."""
    from src.config import Settings

    s = Settings(
        _env_file=None,  # Disable .env loading for test
        anthropic_api_key="test-key",
    )
    assert s.anthropic_api_key == "test-key"
    assert s.awx_host == "http://localhost:8052"
    assert s.webhook_port == 8000
    assert s.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


def test_settings_no_hardcoded_secrets():
    """Default settings must NOT contain real credentials."""
    from src.config import Settings

    s = Settings(_env_file=None)
    assert s.anthropic_api_key == ""
    assert s.servicenow_password == ""
    assert s.slack_bot_token == ""
    assert s.github_token == ""
    assert s.awx_password == ""
    assert s.ansible_vault_password == ""


def test_settings_from_env_vars(monkeypatch):
    """Settings should read from environment variables."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-123")
    monkeypatch.setenv("SERVICENOW_INSTANCE", "https://test.service-now.com")
    monkeypatch.setenv("WEBHOOK_PORT", "9000")

    from src.config import Settings

    s = Settings(_env_file=None)
    assert s.anthropic_api_key == "sk-ant-test-123"
    assert s.servicenow_instance == "https://test.service-now.com"
    assert s.webhook_port == 9000
