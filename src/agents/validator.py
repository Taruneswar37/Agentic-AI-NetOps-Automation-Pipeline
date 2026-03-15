"""
Agentic NetOps — Agent 3: Validator
Runs pre-execution checks (ICMP ping + SSH test) against the target device
via Ansible AWX, then sends Slack approval request (Gate 2).
"""

from __future__ import annotations

from typing import Any

from src.config import settings
from src.integrations.awx import AWXClient
from src.integrations.slack import SlackClient
from src.integrations.servicenow import ServiceNowClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ValidatorAgent:
    """
    Agent 3 — Validator.

    Workflow:
        1. Trigger AWX pre-check job (ICMP ping + SSH connectivity)
        2. Poll for results
        3. If both pass → send Slack approval (Gate 2)
        4. If either fails → notify engineer with diagnostics, stop pipeline.
    """

    def __init__(self) -> None:
        pass

    @property
    def awx_client(self) -> AWXClient:
        return AWXClient()

    @property
    def slack_client(self) -> SlackClient:
        return SlackClient()

    @property
    def snow_client(self) -> ServiceNowClient:
        return ServiceNowClient()

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the Validator agent.

        Args:
            state: LangGraph shared state with 'task_payload' and 'playbook_path'.

        Returns:
            Updated state with 'pre_check_results' and approval status.
        """
        task = state.get("task_payload", {})
        ticket_number = task.get("ticket_number", "UNKNOWN")
        device_ip = task.get("device_ip", "")
        device_name = task.get("device_name", "")

        logger.info(
            "Validator started",
            extra={"agent": "validator", "ticket": ticket_number, "device": device_name},
        )

        # ── Step 1: Trigger pre-check job in AWX ──
        pre_check_job = await self.awx_client.launch_job(
            template_name="netops-pre-check",
            extra_vars={
                "target_host": device_ip,
                "device_name": device_name,
                "ticket_number": ticket_number,
            },
        )

        if not pre_check_job:
            state["error"] = "Failed to launch AWX pre-check job"
            state["status"] = "failed"
            return state

        # ── Step 2: Poll for results ──
        job_result = await self.awx_client.wait_for_job(pre_check_job["id"])

        pre_check_results = {
            "icmp_ping": job_result.get("icmp_ping", False),
            "ssh_test": job_result.get("ssh_test", False),
            "job_id": pre_check_job["id"],
            "raw_output": job_result.get("stdout", ""),
        }

        state["pre_check_results"] = pre_check_results

        # ── Step 3: Evaluate results ──
        ping_ok = pre_check_results["icmp_ping"]
        ssh_ok = pre_check_results["ssh_test"]

        if not ping_ok or not ssh_ok:
            # Pre-checks failed — notify and stop
            failure_details = []
            if not ping_ok:
                failure_details.append("ICMP ping FAILED — device may be unreachable")
            if not ssh_ok:
                failure_details.append("SSH test FAILED — device may not be manageable")

            await self.slack_client.send_failure_notification(
                ticket_number=ticket_number,
                device_name=device_name,
                details=failure_details,
            )

            await self.snow_client.update_ticket(
                ticket_number=ticket_number,
                work_notes=f"Pre-checks failed: {'; '.join(failure_details)}",
            )

            state["error"] = f"Pre-checks failed: {'; '.join(failure_details)}"
            state["status"] = "pre_check_failed"

            logger.warning(
                "Pre-checks failed",
                extra={"agent": "validator", "ticket": ticket_number},
            )
            return state

        # ── Step 4: Both passed — send Slack approval (Gate 2) ──
        await self.slack_client.send_approval_request(
            gate="gate_2",
            ticket_number=ticket_number,
            summary=f"Pre-checks PASSED for {device_name} ({device_ip}). Ready to push configuration.",
            details={
                "icmp_ping": "✓ PASS",
                "ssh_test": "✓ PASS",
                "playbook": state.get("playbook_path", ""),
            },
        )

        state["current_agent"] = "validator"
        state["status"] = "awaiting_approval_gate_2"

        logger.info(
            "Pre-checks passed, awaiting Gate 2 approval",
            extra={"agent": "validator", "ticket": ticket_number},
        )
        return state
