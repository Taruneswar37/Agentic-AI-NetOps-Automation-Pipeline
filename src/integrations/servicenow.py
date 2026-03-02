"""
Agentic NetOps — ServiceNow REST API Client
Handles reading, updating, and closing change request tickets.
"""

from __future__ import annotations

from typing import Any

import httpx

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ServiceNow Change Request table API path
CHANGE_TABLE = "/api/now/table/change_request"


class ServiceNowClient:
    """
    Client for ServiceNow Change Request operations.

    All credentials come from environment settings — never hardcoded.
    Credentials are read lazily at method call time, not at init.
    """

    def __init__(self) -> None:
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def base_url(self) -> str:
        return settings.servicenow_instance.rstrip("/")

    @property
    def auth(self) -> tuple[str, str]:
        return (settings.servicenow_username, settings.servicenow_password)

    async def get_ticket(self, ticket_number: str) -> dict[str, Any] | None:
        """
        Fetch a change request ticket by its number.

        Args:
            ticket_number: The change request number (e.g., "CHG0012345").

        Returns:
            Ticket data dict, or None if not found.
        """
        url = f"{self.base_url}{CHANGE_TABLE}"
        params = {
            "sysparm_query": f"number={ticket_number}",
            "sysparm_limit": "1",
        }

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    url, params=params, auth=self.auth, headers=self.headers, timeout=30.0
                )
                response.raise_for_status()
                results = response.json().get("result", [])
                if results:
                    logger.info("Ticket fetched", extra={"ticket": ticket_number})
                    return results[0]
                logger.warning("Ticket not found", extra={"ticket": ticket_number})
                return None
        except httpx.HTTPError as e:
            logger.error("ServiceNow API error", extra={"error": str(e)})
            return None

    async def update_ticket(
        self, ticket_number: str, work_notes: str, state: str | None = None
    ) -> bool:
        """
        Update a change request with work notes and optional state change.

        Args:
            ticket_number: The change request number.
            work_notes: Notes to append to the ticket's work notes.
            state: Optional state value (e.g., "implement" = -1).

        Returns:
            True if update was successful.
        """
        sys_id = await self._get_sys_id(ticket_number)
        if not sys_id:
            return False

        url = f"{self.base_url}{CHANGE_TABLE}/{sys_id}"
        payload: dict[str, Any] = {"work_notes": work_notes}
        if state:
            payload["state"] = state

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.patch(
                    url, json=payload, auth=self.auth, headers=self.headers, timeout=30.0
                )
                response.raise_for_status()
                logger.info("Ticket updated", extra={"ticket": ticket_number})
                return True
        except httpx.HTTPError as e:
            logger.error("Failed to update ticket", extra={"error": str(e)})
            return False

    async def close_ticket(self, ticket_number: str, close_notes: str) -> bool:
        """
        Close a change request as successfully implemented.

        Args:
            ticket_number: The change request number.
            close_notes: Closing notes describing what was done.

        Returns:
            True if the ticket was closed successfully.
        """
        return await self.update_ticket(
            ticket_number=ticket_number,
            work_notes=f"[AUTO-CLOSED] {close_notes}",
            state="closed",  # ServiceNow closed state
        )

    async def _get_sys_id(self, ticket_number: str) -> str | None:
        """Resolve a ticket number to its ServiceNow sys_id."""
        ticket = await self.get_ticket(ticket_number)
        return ticket.get("sys_id") if ticket else None
