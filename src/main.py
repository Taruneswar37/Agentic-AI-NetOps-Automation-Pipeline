"""
Agentic NetOps — Main Entry Point
Starts the LangGraph pipeline for processing a ServiceNow change request.
"""

from __future__ import annotations

import asyncio
import sys

from rich.console import Console

from src.config import settings
from src.graph.orchestrator import build_pipeline
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


async def run_pipeline(ticket_number: str | None = None) -> None:
    """
    Run the NetOps automation pipeline.

    Args:
        ticket_number: Optional ServiceNow ticket number (e.g., "CHG0012345").
                       If not provided, the pipeline will poll for new tickets.
    """
    console.print(
        "\n[bold cyan]═══════════════════════════════════════[/bold cyan]"
    )
    console.print(
        "[bold cyan]  Agentic NetOps — Pipeline Starting   [/bold cyan]"
    )
    console.print(
        "[bold cyan]═══════════════════════════════════════[/bold cyan]\n"
    )

    # Validate critical settings
    missing = []
    if not settings.anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY")
    if not settings.servicenow_instance:
        missing.append("SERVICENOW_INSTANCE")
    if not settings.slack_bot_token:
        missing.append("SLACK_BOT_TOKEN")

    if missing:
        console.print(
            f"[bold red]✗ Missing required environment variables: {', '.join(missing)}[/bold red]"
        )
        console.print("[dim]  → Copy .env.example to .env and fill in your values[/dim]")
        sys.exit(1)

    # Build and invoke the LangGraph pipeline
    pipeline = build_pipeline()

    initial_state = {
        "ticket_number": ticket_number or "",
        "current_agent": "planner",
        "status": "started",
        "messages": [],
        "task_payload": {},
        "playbook_content": "",
        "playbook_path": "",
        "pre_check_results": {},
        "post_check_results": {},
        "approval_gate_1": None,
        "approval_gate_2": None,
        "error": None,
    }

    logger.info("Pipeline started", extra={"ticket": ticket_number})
    console.print(f"[green]▶ Processing ticket:[/green] {ticket_number or 'polling mode'}")

    try:
        result = await pipeline.ainvoke(initial_state)
        logger.info("Pipeline completed", extra={"status": result.get("status")})
        console.print(f"\n[bold green]✓ Pipeline finished — status: {result.get('status')}[/bold green]")
    except Exception as e:
        logger.error("Pipeline failed", extra={"error": str(e)})
        console.print(f"\n[bold red]✗ Pipeline failed: {e}[/bold red]")
        raise


def main() -> None:
    """CLI entry point."""
    ticket = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(run_pipeline(ticket))


if __name__ == "__main__":
    main()
