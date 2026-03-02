"""
Agentic NetOps — Agent 1: Planner
Reads a ServiceNow ticket, extracts structured task details,
validates against compliance policies via RAG, and sends a
Slack approval request (Gate 1).
"""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import settings
from src.integrations.servicenow import ServiceNowClient
from src.integrations.slack import SlackClient
from src.rag.query import query_knowledge_base
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── System prompt for the Planner LLM ──
PLANNER_SYSTEM_PROMPT = """You are a network operations planner AI agent.

Your job is to analyze a ServiceNow change request ticket and extract the
following structured information:

1. device_name — the target network device (e.g., "Firewall-NYC-01")
2. device_ip — the IP address of the device
3. device_type — one of: cisco_ios, paloalto_panos, juniper_junos
4. action — the change action (e.g., "open_port", "close_port", "add_acl")
5. port — the port number (if applicable)
6. protocol — tcp or udp (if applicable)
7. direction — inbound or outbound (if applicable)
8. description — a human-readable summary of the change

Return your response as a valid JSON object with exactly these fields.
If a field is not applicable, set it to null.
Do NOT invent information that is not in the ticket.
"""


class PlannerAgent:
    """
    Agent 1 — Planner.

    Workflow:
        1. Fetch the ticket from ServiceNow
        2. Parse it with Claude to extract structured task details
        3. Validate against compliance policies via RAG
        4. Send Slack approval request (Gate 1)
        5. Return structured task payload on approval
    """

    def __init__(self) -> None:
        pass

    @property
    def llm(self) -> ChatAnthropic:
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0,
            max_tokens=2048,
        )

    @property
    def snow_client(self) -> ServiceNowClient:
        return ServiceNowClient()

    @property
    def slack_client(self) -> SlackClient:
        return SlackClient()

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the Planner agent.
        """
        ticket_number = state.get("ticket_number", "UNKNOWN")
        logger.info("Planner started", extra={"agent": "planner", "ticket": ticket_number})

        # ── Step 1: Fetch ticket or use provided description ──
        ticket_description = state.get("ticket_description")
        ticket_short = state.get("ticket_short_description", "")

        if not ticket_description:
            ticket_data = await self.snow_client.get_ticket(ticket_number)
            if not ticket_data:
                state["error"] = f"Ticket {ticket_number} not found in ServiceNow"
                state["status"] = "failed"
                return state
            ticket_description = ticket_data.get("description", "")
            ticket_short = ticket_data.get("short_description", "")

        # ── Step 2: Parse with LLM ──
        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Ticket Number: {ticket_number}\n"
                f"Short Description: {ticket_short}\n"
                f"Full Description: {ticket_description}"
            ),
        ]

        response = await self.llm.ainvoke(messages)
        task_payload = self._parse_llm_response(response.content)

        if not task_payload:
            state["error"] = "Failed to parse task details from ticket"
            state["status"] = "failed"
            return state

        task_payload["ticket_number"] = ticket_number

        # ── Step 3: Compliance check via RAG ──
        compliance_query = (
            f"Is it compliant to {task_payload.get('action', 'modify')} "
            f"port {task_payload.get('port', 'N/A')} "
            f"({task_payload.get('protocol', 'tcp')}) "
            f"on a {task_payload.get('device_type', 'network')} device? "
            f"Direction: {task_payload.get('direction', 'inbound')}"
        )
        compliance_context = query_knowledge_base(compliance_query, top_k=3)
        
        # Simple evaluation of compliance
        # In a real scenario, use another LLM call to evaluate the context
        is_compliant = "allowed" in compliance_context.lower() and "prohibit" not in compliance_context.lower()
        
        state["task_payload"] = task_payload
        state["compliance_check_passed"] = is_compliant
        state["compliance_notes"] = compliance_context
        
        # Copy fields to top level for convenience/orchestrator
        state.update({
            "device_name": task_payload.get("device_name"),
            "device_ip": task_payload.get("device_ip"),
            "device_type": task_payload.get("device_type"),
            "change_type": task_payload.get("action"),
            "port": task_payload.get("port"),
            "protocol": task_payload.get("protocol"),
            "direction": task_payload.get("direction"),
        })

        logger.info(
            "Task parsed and compliance checked",
            extra={"agent": "planner", "ticket": ticket_number, "compliant": is_compliant},
        )

        # ── Step 4: Send Slack approval (Gate 1) ──
        # Only send if not specifically told to skip (for tests)
        if not state.get("skip_slack"):
            await self.slack_client.send_approval_request(
                gate="gate_1",
                ticket_number=ticket_number,
                summary=task_payload.get("description", ticket_short),
                details={**task_payload, "compliance_check_passed": is_compliant},
            )

        state["current_agent"] = "planner"
        state["status"] = "awaiting_approval_gate_1"
        return state

    def _parse_llm_response(self, content: str) -> dict[str, Any] | None:
        """Parse the LLM JSON response into a dict."""
        import json

        try:
            # Handle markdown-wrapped JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            logger.error("Failed to parse LLM response", extra={"agent": "planner"})
            return None
