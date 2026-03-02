"""
Agentic NetOps — Agent 2: Coder
Generates a production-ready Ansible playbook for the requested change,
using RAG to look up device-specific syntax, and commits it to GitHub.
"""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import settings
from src.integrations.github_client import GitHubClient
from src.rag.query import query_knowledge_base
from src.utils.logger import get_logger
from src.utils.vault import build_vault_vars_block

logger = get_logger(__name__)

# ── System prompt for the Coder LLM ──
CODER_SYSTEM_PROMPT = """You are a network automation engineer AI agent.

Your job is to generate a complete, production-ready Ansible playbook
for the given network change task.

CRITICAL RULES:
1. NEVER hardcode any credentials (usernames, passwords, enable secrets).
2. ALWAYS use Ansible Vault variable references for credentials:
   - ansible_user: "{{ vault_device_username }}"
   - ansible_password: "{{ vault_device_password }}"
   - ansible_become_password: "{{ vault_enable_password }}"
3. Use the correct Ansible module for the device type:
   - cisco_ios → cisco.ios.ios_acls, cisco.ios.ios_config
   - paloalto_panos → paloaltonetworks.panos modules
   - juniper_junos → junipernetworks.junos modules
4. Include proper connection settings (network_cli, ansible_network_os, etc.)
5. Add the ticket number as a comment in the playbook header.
6. The playbook must be idempotent.

Return ONLY the YAML content of the playbook — no markdown, no explanation.
"""


class CoderAgent:
    """
    Agent 2 — Coder.

    Workflow:
        1. Query RAG for device-specific Ansible syntax
        2. Generate a complete Ansible playbook via Claude
        3. Inject vault variable references (safety net)
        4. Commit the playbook to GitHub
    """

    def __init__(self) -> None:
        pass

    @property
    def llm(self) -> ChatAnthropic:
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0,
            max_tokens=4096,
        )

    @property
    def github_client(self) -> GitHubClient:
        return GitHubClient()

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the Coder agent.

        Args:
            state: LangGraph shared state containing 'task_payload' from Planner.

        Returns:
            Updated state with 'playbook_content' and 'playbook_path' populated.
        """
        task = state.get("task_payload", {})
        ticket_number = task.get("ticket_number", "UNKNOWN")
        logger.info("Coder started", extra={"agent": "coder", "ticket": ticket_number})

        # ── Step 1: Query RAG for device-specific syntax ──
        device_type = task.get("device_type", "cisco_ios")
        rag_query = (
            f"Show me the correct Ansible playbook syntax for {device_type} "
            f"to {task.get('action', 'configure')} "
            f"port {task.get('port', '443')} "
            f"protocol {task.get('protocol', 'tcp')} "
            f"direction {task.get('direction', 'inbound')}. "
            f"Include the correct Ansible module name and connection settings."
        )
        ansible_reference = query_knowledge_base(rag_query, top_k=3)

        # ── Step 2: Generate playbook with LLM ──
        vault_vars = build_vault_vars_block()
        messages = [
            SystemMessage(content=CODER_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"TASK DETAILS:\n{_format_task(task)}\n\n"
                    f"ANSIBLE REFERENCE (from knowledge base):\n{ansible_reference}\n\n"
                    f"VAULT VARIABLES TO USE:\n"
                    f"  ansible_user: {vault_vars['ansible_user']}\n"
                    f"  ansible_password: {vault_vars['ansible_password']}\n"
                    f"  ansible_become_password: {vault_vars['ansible_become_password']}\n"
                )
            ),
        ]

        response = await self.llm.ainvoke(messages)
        playbook_content = self._clean_playbook(response.content)

        # ── Step 3: Safety check — reject if hardcoded credentials found ──
        if self._contains_hardcoded_creds(playbook_content):
            state["error"] = "Generated playbook contains hardcoded credentials — rejected"
            state["status"] = "failed"
            logger.error("Hardcoded creds detected", extra={"agent": "coder"})
            return state

        # ── Step 4: Commit to GitHub ──
        playbook_filename = f"{ticket_number.lower().replace(' ', '_')}_playbook.yml"
        playbook_path = f"playbooks/{playbook_filename}"

        commit_result = await self.github_client.commit_file(
            path=playbook_path,
            content=playbook_content,
            message=f"[{ticket_number}] Auto-generated playbook for {task.get('action', 'change')} on {task.get('device_name', 'device')}",
        )

        state["playbook_content"] = playbook_content
        state["playbook_path"] = playbook_path
        state["current_agent"] = "coder"
        state["status"] = "playbook_generated"

        logger.info(
            "Playbook generated and committed",
            extra={
                "agent": "coder",
                "ticket": ticket_number,
                "path": playbook_path,
            },
        )
        return state

    def _clean_playbook(self, content: str) -> str:
        """Strip markdown fences if the LLM wrapped the YAML."""
        if "```yaml" in content:
            content = content.split("```yaml")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return content.strip() + "\n"

    def _contains_hardcoded_creds(self, content: str) -> bool:
        """Check for obvious hardcoded passwords/secrets in the playbook."""
        danger_patterns = [
            "password:",
            "ansible_password:",
            "ansible_ssh_pass:",
            "become_pass:",
        ]
        for line in content.splitlines():
            stripped = line.strip().lower()
            for pattern in danger_patterns:
                if pattern in stripped and "vault_" not in stripped and "{{" not in stripped:
                    return True
        return False


def _format_task(task: dict[str, Any]) -> str:
    """Format task payload for the LLM prompt."""
    lines = []
    for key, value in task.items():
        if key != "compliance_context" and value is not None:
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)
