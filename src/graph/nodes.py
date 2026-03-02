"""
Agentic NetOps — LangGraph Node Functions
Each function wraps an agent and connects to the graph orchestrator.
"""

from __future__ import annotations

from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


async def planner_node(state: dict[str, Any]) -> dict[str, Any]:
    """Run the Planner agent."""
    from src.agents.planner import PlannerAgent

    logger.info("Entering planner node", extra={"agent": "planner"})
    agent = PlannerAgent()
    return await agent.run(state)


async def coder_node(state: dict[str, Any]) -> dict[str, Any]:
    """Run the Coder agent."""
    from src.agents.coder import CoderAgent

    logger.info("Entering coder node", extra={"agent": "coder"})
    agent = CoderAgent()
    return await agent.run(state)


async def validator_node(state: dict[str, Any]) -> dict[str, Any]:
    """Run the Validator agent."""
    from src.agents.validator import ValidatorAgent

    logger.info("Entering validator node", extra={"agent": "validator"})
    agent = ValidatorAgent()
    return await agent.run(state)


async def executor_node(state: dict[str, Any]) -> dict[str, Any]:
    """Run the Executor agent."""
    from src.agents.executor import ExecutorAgent

    logger.info("Entering executor node", extra={"agent": "executor"})
    agent = ExecutorAgent()
    return await agent.run(state)


async def rejection_node(state: dict[str, Any]) -> dict[str, Any]:
    """Handle a rejected approval — update ServiceNow and stop."""
    from src.integrations.servicenow import ServiceNowClient

    ticket = state.get("ticket_number", "UNKNOWN")
    gate = "Gate 1" if state.get("approval_gate_1") is False else "Gate 2"

    snow = ServiceNowClient()
    await snow.update_ticket(
        ticket_number=ticket,
        work_notes=f"Change rejected at {gate}. Pipeline stopped.",
    )

    state["status"] = "rejected"
    state["error"] = f"Rejected at {gate}"
    logger.info("Change rejected", extra={"ticket": ticket, "action": gate})
    return state


# ── Routing functions (used by conditional edges) ──

def route_after_planner(state: dict[str, Any]) -> str:
    """Route after Planner: wait for Gate 1 approval."""
    if state.get("status") == "failed":
        return "end"
    return "wait_for_gate_1"


def route_after_gate_1(state: dict[str, Any]) -> str:
    """Route after Gate 1 approval callback."""
    if state.get("approval_gate_1") is True:
        return "coder"
    return "rejection"


def route_after_validator(state: dict[str, Any]) -> str:
    """Route after Validator: wait for Gate 2 or handle pre-check failure."""
    if state.get("status") == "pre_check_failed":
        return "end"
    if state.get("status") == "failed":
        return "end"
    return "wait_for_gate_2"


def route_after_gate_2(state: dict[str, Any]) -> str:
    """Route after Gate 2 approval callback."""
    if state.get("approval_gate_2") is True:
        return "executor"
    return "rejection"
