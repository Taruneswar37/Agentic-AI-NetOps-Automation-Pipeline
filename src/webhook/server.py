"""
Agentic NetOps — FastAPI Webhook Server
Receives Slack interactive message callbacks and resumes the paused pipeline.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Agentic NetOps Webhook Server",
    description="Receives Slack approval callbacks and resumes the automation pipeline.",
    version="0.1.0",
)

# ── In-memory store for pending approvals ──
# In production, replace with Redis or a database.
# Format: { "ticket_number": { "gate": "gate_1", "callback": <coroutine_handle> } }
_pending_approvals: dict[str, dict[str, Any]] = {}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "agentic-netops-webhook"}


@app.post("/slack/interactions")
async def slack_interaction(request: Request) -> JSONResponse:
    """
    Handle Slack interactive message callbacks.

    Slack sends a POST request when a user clicks an Approve or Reject button.
    This endpoint verifies the request, extracts the action, and resumes
    the paused pipeline.
    """
    # ── Verify Slack request signature ──
    body = await request.body()
    if not _verify_slack_signature(request, body):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    # ── Parse the payload ──
    try:
        form_data = await request.form()
        payload = json.loads(form_data.get("payload", "{}"))
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Failed to parse Slack payload", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail="Invalid payload")

    # ── Extract action details ──
    actions = payload.get("actions", [])
    if not actions:
        return JSONResponse({"text": "No action received"})

    action = actions[0]
    action_id = action.get("action_id", "")          # e.g., "approve_gate_1"
    ticket_number = action.get("value", "")           # The ticket number
    user = payload.get("user", {}).get("name", "unknown")

    # Determine gate and decision
    is_approval = action_id.startswith("approve_")
    gate = action_id.replace("approve_", "").replace("reject_", "")  # "gate_1" or "gate_2"

    logger.info(
        "Slack callback received",
        extra={
            "ticket": ticket_number,
            "action": "approved" if is_approval else "rejected",
            "status": gate,
        },
    )

    # ── Store the decision for the pipeline to pick up ──
    _pending_approvals[f"{ticket_number}_{gate}"] = {
        "approved": is_approval,
        "user": user,
        "timestamp": time.time(),
    }

    # ── Respond to Slack ──
    decision_text = "✅ Approved" if is_approval else "❌ Rejected"
    return JSONResponse({
        "response_type": "in_channel",
        "replace_original": True,
        "text": f"{decision_text} by @{user} for `{ticket_number}` ({gate})",
    })


@app.get("/approvals/{ticket_number}/{gate}")
async def get_approval_status(ticket_number: str, gate: str) -> dict[str, Any]:
    """
    Check the approval status for a specific ticket and gate.

    The LangGraph pipeline can poll this endpoint to check if an
    approval decision has been made.
    """
    key = f"{ticket_number}_{gate}"
    if key in _pending_approvals:
        return {"found": True, **_pending_approvals[key]}
    return {"found": False}


def _verify_slack_signature(request: Request, body: bytes) -> bool:
    """
    Verify that the request came from Slack using request signing.

    Slack sends a signature in the X-Slack-Signature header that we
    verify against our signing secret.
    """
    signing_secret = settings.slack_signing_secret
    if not signing_secret:
        logger.warning("No Slack signing secret configured — skipping verification")
        return True  # Allow in development

    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    slack_signature = request.headers.get("X-Slack-Signature", "")

    # Reject requests older than 5 minutes (replay attack protection)
    if abs(time.time() - float(timestamp or 0)) > 300:
        return False

    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    my_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(my_signature, slack_signature)


# ── Run with: uvicorn src.webhook.server:app --host 0.0.0.0 --port 8000 ──
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.webhook.server:app",
        host=settings.webhook_host,
        port=settings.webhook_port,
        reload=True,
    )
