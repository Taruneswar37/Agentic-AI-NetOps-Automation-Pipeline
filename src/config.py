"""
Agentic NetOps — Configuration
Loads all settings from environment variables via .env file.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ──
    anthropic_api_key: str = ""

    # ── ServiceNow ──
    servicenow_instance: str = ""
    servicenow_username: str = ""
    servicenow_password: str = ""

    # ── Slack ──
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_approval_channel: str = ""

    # ── GitHub ──
    github_token: str = ""
    github_repo_owner: str = ""
    github_repo_name: str = ""

    # ── Ansible AWX ──
    awx_host: str = "http://localhost:8052"
    awx_username: str = "admin"
    awx_password: str = ""
    awx_verify_ssl: bool = False

    # ── Ansible Vault ──
    ansible_vault_password: str = ""

    # ── RAG / Knowledge Base ──
    chroma_db_path: str = "./chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Webhook Server ──
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000


# Singleton instance — import this wherever settings are needed
settings = Settings()
