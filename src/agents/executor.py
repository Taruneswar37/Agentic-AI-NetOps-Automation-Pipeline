"""
Agentic NetOps — Agent 4: Executor + Post-Validator
Executes the Ansible playbook via AWX, runs post-checks
(ICMP ping + TCP port test), and closes or rolls back the ticket.
"""

from __future__ import annotations

from typing import Any

from src.config import settings
from src.integrations.awx import AWXClient
from src.integrations.servicenow import ServiceNowClient
from src.integrations.slack import SlackClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutorAgent:
    """
    Agent 4 — Executor + Post-Validator.

    Workflow:
        1. Trigger AWX job to execute the Ansible playbook
        2. Poll for completion
        3. Run post-checks (ICMP ping + TCP port connectivity)
        4. If post-checks pass → close ticket, post success to Slack
        5. If post-checks fail → trigger rollback, update ticket, alert team
    """

    def __init__(self) -> None:
        pass

    @property
    def awx_client(self) -> AWXClient:
        return AWXClient()

    @property
    def snow_client(self) -> ServiceNowClient:
        return ServiceNowClient()

    @property
    def slack_client(self) -> SlackClient:
        return SlackClient()

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the Executor agent.

        Args:
            state: LangGraph shared state with full pipeline context.

        Returns:
            Updated state with final status (completed/rollback_triggered).
        """
        task = state.get("task_payload", {})
        ticket_number = task.get("ticket_number", "UNKNOWN")
        device_ip = task.get("device_ip", "")
        device_name = task.get("device_name", "")
        port = task.get("port")

        logger.info(
            "Executor started",
            extra={"agent": "executor", "ticket": ticket_number},
        )

        # ── Step 1: Execute the playbook via AWX ──
        exec_job = await self.awx_client.launch_job(
            template_name="netops-execute",
            extra_vars={
                "target_host": device_ip,
                "device_name": device_name,
                "ticket_number": ticket_number,
                "playbook_path": state.get("playbook_path", ""),
            },
        )

        if not exec_job:
            state["error"] = "Failed to launch AWX execution job"
            state["status"] = "failed"
            return state

        exec_result = await self.awx_client.wait_for_job(exec_job["id"])

        if exec_result.get("status") != "successful":
            await self._handle_failure(
                state, ticket_number, device_name,
                reason=f"Playbook execution failed: {exec_result.get('stdout', 'unknown error')}",
            )
            return state

        # ── Step 2: Run post-checks ──
        post_check_job = await self.awx_client.launch_job(
            template_name="netops-post-check",
            extra_vars={
                "target_host": device_ip,
                "device_name": device_name,
                "ticket_number": ticket_number,
                "check_port": port,
                "check_protocol": task.get("protocol", "tcp"),
            },
        )

        post_result = await self.awx_client.wait_for_job(post_check_job["id"])

        post_check_results = {
            "icmp_ping": post_result.get("icmp_ping", False),
            "tcp_port_check": post_result.get("tcp_port_check", False),
            "job_id": post_check_job["id"],
        }

        state["post_check_results"] = post_check_results

        ping_ok = post_check_results["icmp_ping"]
        port_ok = post_check_results["tcp_port_check"]

        if not ping_ok or not port_ok:
            # ── Post-checks failed → Rollback ──
            failure_reasons = []
            if not ping_ok:
                failure_reasons.append("Post-check ICMP ping FAILED")
            if not port_ok:
                failure_reasons.append(f"Post-check TCP port {port} connectivity FAILED")

            await self._handle_failure(
                state, ticket_number, device_name,
                reason="; ".join(failure_reasons),
                rollback=True,
            )
            return state

        # ── Step 3: All passed → Close ticket ──
        await self.snow_client.close_ticket(
            ticket_number=ticket_number,
            close_notes=(
                f"Change completed successfully.\n"
                f"Device: {device_name} ({device_ip})\n"
                f"Action: {task.get('action', 'N/A')}\n"
                f"Port: {port} ({task.get('protocol', 'tcp')})\n"
                f"Post-checks: ICMP ✓ | TCP Port {port} ✓"
            ),
        )

        await self.slack_client.send_success_notification(
            ticket_number=ticket_number,
            device_name=device_name,
            summary=f"✅ Change completed — port {port} is now live on {device_name}",
        )

        state["current_agent"] = "executor"
        state["status"] = "completed"

        logger.info(
            "Pipeline completed successfully",
            extra={"agent": "executor", "ticket": ticket_number},
        )
        return state

    async def _handle_failure(
        self,
        state: dict[str, Any],
        ticket_number: str,
        device_name: str,
        reason: str,
        rollback: bool = False,
    ) -> None:
        """Handle execution or post-check failure with optional rollback."""
        logger.error(
            "Execution failed",
            extra={"agent": "executor", "ticket": ticket_number, "error": reason},
        )

        if rollback:
            # Trigger rollback playbook
            rollback_job = await self.awx_client.launch_job(
                template_name="netops-rollback",
                extra_vars={
                    "target_host": state["task_payload"].get("device_ip", ""),
                    "ticket_number": ticket_number,
                },
            )
            if rollback_job:
                await self.awx_client.wait_for_job(rollback_job["id"])
                logger.info("Rollback completed", extra={"agent": "executor", "ticket": ticket_number})

        await self.snow_client.update_ticket(
            ticket_number=ticket_number,
            work_notes=f"FAILURE: {reason}" + (" | Rollback executed." if rollback else ""),
        )

        await self.slack_client.send_failure_notification(
            ticket_number=ticket_number,
            device_name=device_name,
            details=[reason] + (["Rollback has been executed."] if rollback else []),
        )

        state["error"] = reason
        state["status"] = "rollback_triggered" if rollback else "failed"
