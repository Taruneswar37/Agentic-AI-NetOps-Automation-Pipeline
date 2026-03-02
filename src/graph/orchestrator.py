"""
Agentic NetOps — LangGraph Pipeline Orchestrator
Builds the stateful multi-agent graph with human-in-the-loop interrupt support.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from src.graph.state import PipelineState
from src.graph.nodes import (
    planner_node,
    coder_node,
    validator_node,
    executor_node,
    rejection_node,
    route_after_planner,
    route_after_gate_1,
    route_after_validator,
    route_after_gate_2,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_pipeline() -> StateGraph:
    """
    Build and compile the LangGraph pipeline.

    Graph structure:
        START → planner → [wait_for_gate_1] → coder → validator → [wait_for_gate_2] → executor → END
                                ↓                                        ↓
                            rejection → END                          rejection → END

    Human-in-the-loop:
        The graph uses LangGraph's `interrupt_before` to pause at the
        approval gate nodes. The FastAPI webhook server resumes the
        graph when a Slack callback is received.

    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    graph = StateGraph(PipelineState)

    # ── Add nodes ──
    graph.add_node("planner", planner_node)
    graph.add_node("wait_for_gate_1", _gate_1_passthrough)
    graph.add_node("coder", coder_node)
    graph.add_node("validator", validator_node)
    graph.add_node("wait_for_gate_2", _gate_2_passthrough)
    graph.add_node("executor", executor_node)
    graph.add_node("rejection", rejection_node)

    # ── Set entry point ──
    graph.set_entry_point("planner")

    # ── Edges ──
    # After planner: route to gate 1 wait or end on failure
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "wait_for_gate_1": "wait_for_gate_1",
            "end": END,
        },
    )

    # After gate 1: route to coder (approved) or rejection (rejected)
    graph.add_conditional_edges(
        "wait_for_gate_1",
        route_after_gate_1,
        {
            "coder": "coder",
            "rejection": "rejection",
        },
    )

    # Coder → Validator (always, unless coder fails — handled in node)
    graph.add_edge("coder", "validator")

    # After validator: route to gate 2 wait or end on pre-check failure
    graph.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "wait_for_gate_2": "wait_for_gate_2",
            "end": END,
        },
    )

    # After gate 2: route to executor (approved) or rejection (rejected)
    graph.add_conditional_edges(
        "wait_for_gate_2",
        route_after_gate_2,
        {
            "executor": "executor",
            "rejection": "rejection",
        },
    )

    # Executor and rejection both end the pipeline
    graph.add_edge("executor", END)
    graph.add_edge("rejection", END)

    # ── Compile with interrupt points ──
    # The pipeline pauses BEFORE these nodes, waiting for webhook callback
    compiled = graph.compile(
        interrupt_before=["wait_for_gate_1", "wait_for_gate_2"],
    )

    logger.info("Pipeline graph compiled successfully")
    return compiled


async def _gate_1_passthrough(state: dict) -> dict:
    """
    Gate 1 passthrough node.

    This node exists solely as an interrupt point.
    When the pipeline resumes after a Slack callback,
    the approval_gate_1 field will have been set.
    """
    return state


async def _gate_2_passthrough(state: dict) -> dict:
    """
    Gate 2 passthrough node.

    Same pattern as Gate 1 — exists as an interrupt point.
    """
    return state
