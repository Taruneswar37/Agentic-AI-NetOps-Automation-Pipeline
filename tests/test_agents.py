"""
Tests for agent modules — import and instantiation checks.
"""

import pytest


def test_planner_agent_imports():
    """PlannerAgent should import without errors."""
    from src.agents.planner import PlannerAgent

    assert PlannerAgent is not None


def test_coder_agent_imports():
    """CoderAgent should import without errors."""
    from src.agents.coder import CoderAgent

    assert CoderAgent is not None


def test_validator_agent_imports():
    """ValidatorAgent should import without errors."""
    from src.agents.validator import ValidatorAgent

    assert ValidatorAgent is not None


def test_executor_agent_imports():
    """ExecutorAgent should import without errors."""
    from src.agents.executor import ExecutorAgent

    assert ExecutorAgent is not None


def test_pipeline_state_schema():
    """PipelineState schema should define all required fields."""
    from src.graph.state import PipelineState

    # Verify expected keys exist in annotations
    annotations = PipelineState.__annotations__
    expected_keys = [
        "ticket_number",
        "current_agent",
        "status",
        "task_payload",
        "playbook_content",
        "playbook_path",
        "pre_check_results",
        "post_check_results",
        "approval_gate_1",
        "approval_gate_2",
        "error",
    ]
    for key in expected_keys:
        assert key in annotations, f"Missing key: {key}"


def test_webhook_app_imports():
    """FastAPI webhook app should import without errors."""
    from src.webhook.server import app

    assert app is not None
    assert app.title == "Agentic NetOps Webhook Server"


def test_coder_hardcoded_creds_check():
    """Coder's credential scanner should catch hardcoded passwords."""
    from src.agents.coder import CoderAgent

    coder = CoderAgent()

    # Should detect hardcoded creds
    bad_playbook = """
    - hosts: all
      vars:
        ansible_password: mysecretpassword
    """
    assert coder._contains_hardcoded_creds(bad_playbook) is True

    # Should allow vault references
    good_playbook = """
    - hosts: all
      vars:
        ansible_password: "{{ vault_device_password }}"
    """
    assert coder._contains_hardcoded_creds(good_playbook) is False
