"""
Agentic NetOps — Slack Integration Client
Sends interactive approval messages (Block Kit) and notifications.
"""

from __future__ import annotations

from typing import Any

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SlackClient:
    """
    Slack client for sending approval requests and notifications.

    Uses Block Kit for interactive Approve/Reject buttons.
    Webhook callbacks are handled by the FastAPI server.
    Credentials are read lazily at method call time, not at init.
    """

    def __init__(self) -> None:
        pass

    @property
    def client(self) -> AsyncWebClient:
        return AsyncWebClient(token=settings.slack_bot_token)

    @property
    def channel(self) -> str:
        return settings.slack_approval_channel

    async def send_approval_request(
        self,
        gate: str,
        ticket_number: str,
        summary: str,
        details: dict[str, Any],
    ) -> bool:
        """
        Send an interactive Slack message with Approve/Reject buttons.

        Args:
            gate: The approval gate identifier ("gate_1" or "gate_2").
            ticket_number: ServiceNow ticket number.
            summary: Human-readable summary of the request.
            details: Additional details to display.

        Returns:
            True if the message was sent successfully.
        """
        gate_label = "🔒 Gate 1 — Compliance Approval" if gate == "gate_1" else "🚀 Gate 2 — Execution Approval"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": gate_label},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Ticket:* `{ticket_number}`\n*Summary:* {summary}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*{k}:* {v}"}
                    for k, v in details.items()
                    if k not in ("compliance_context",) and v is not None
                ][:10],  # Slack limits to 10 fields
            },
            {"type": "divider"},
            {
                "type": "actions",
                "block_id": f"approval_{gate}_{ticket_number}",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve", "emoji": True},
                        "style": "primary",
                        "action_id": f"approve_{gate}",
                        "value": ticket_number,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject", "emoji": True},
                        "style": "danger",
                        "action_id": f"reject_{gate}",
                        "value": ticket_number,
                    },
                ],
            },
        ]

        try:
            await self.client.chat_postMessage(
                channel=self.channel,
                text=f"{gate_label} — {ticket_number}",
                blocks=blocks,
            )
            logger.info("Approval request sent", extra={"ticket": ticket_number, "action": gate})
            return True
        except SlackApiError as e:
            logger.error("Slack API error", extra={"error": str(e)})
            return False

    async def send_success_notification(
        self, ticket_number: str, device_name: str, summary: str
    ) -> bool:
        """Send a success notification to the channel."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"✅ *Change Completed Successfully*\n\n"
                        f"*Ticket:* `{ticket_number}`\n"
                        f"*Device:* {device_name}\n"
                        f"*Summary:* {summary}"
                    ),
                },
            },
        ]

        try:
            await self.client.chat_postMessage(
                channel=self.channel,
                text=f"✅ {ticket_number} completed",
                blocks=blocks,
            )
            return True
        except SlackApiError as e:
            logger.error("Slack notification error", extra={"error": str(e)})
            return False

    async def send_failure_notification(
        self, ticket_number: str, device_name: str, details: list[str]
    ) -> bool:
        """Send a failure/rollback notification to the channel."""
        detail_text = "\n".join(f"• {d}" for d in details)
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"🚨 *Change Failed*\n\n"
                        f"*Ticket:* `{ticket_number}`\n"
                        f"*Device:* {device_name}\n\n"
                        f"*Details:*\n{detail_text}"
                    ),
                },
            },
        ]

        try:
            await self.client.chat_postMessage(
                channel=self.channel,
                text=f"🚨 {ticket_number} failed",
                blocks=blocks,
            )
            return True
        except SlackApiError as e:
            logger.error("Slack notification error", extra={"error": str(e)})
            return False
