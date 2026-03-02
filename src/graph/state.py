"""
Agentic NetOps — LangGraph Shared State Schema
Defines the TypedDict that flows through the entire pipeline.
"""

from __future__ import annotations

from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    """
    Shared state schema for the LangGraph pipeline.

    Every node reads from and writes to this state.
    """

    # ── Ticket Info ──
    ticket_number: str                    # ServiceNow change request number
    current_agent: str                    # Name of the currently active agent
    status: str                           # Pipeline status

    # ── Messages (for LangGraph message history) ──
    messages: list[dict[str, Any]]

    # ── Planner output ──
    task_payload: dict[str, Any]          # Structured task extracted from ticket

    # ── Coder output ──
    playbook_content: str                 # Generated YAML playbook
    playbook_path: str                    # Path in GitHub repo

    # ── Validator output ──
    pre_check_results: dict[str, Any]     # ICMP ping + SSH test results

    # ── Executor output ──
    post_check_results: dict[str, Any]    # ICMP ping + TCP port test results

    # ── Approval gates ──
    approval_gate_1: bool | None          # True = approved, False = rejected, None = pending
    approval_gate_2: bool | None

    # ── Error tracking ──
    error: str | None                     # Error message if pipeline fails
