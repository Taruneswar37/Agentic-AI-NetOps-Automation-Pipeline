# 🌐 Agentic AI-Powered NetOps Automation Pipeline

> **Enterprise-grade, multi-agent AI system that automates the full lifecycle of network change requests — from ticket submission to post-validation and closure — with zero hardcoded credentials and mandatory human approval at every critical gate.**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [The Four AI Agents](#the-four-ai-agents)
- [Tech Stack](#tech-stack)
- [Human Approval Gates](#human-approval-gates)
- [Security Rules](#security-rules)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [RAG Knowledge Base](#rag-knowledge-base)
- [Build Timeline](#build-timeline)
- [Current Status](#current-status)
- [Contributing](#contributing)

---

## Overview

When a network engineer submits a change request ticket in ServiceNow (e.g., *"Open Port 443 on Firewall-NYC-01"*), this pipeline automatically:

1. 📖 Reads the ticket and understands what needs to change
2. 🔒 Checks compliance against security policies via RAG
3. 💬 Sends an interactive Slack approval request to the network lead
4. 📝 Generates a production-ready Ansible playbook for the target device
5. 📦 Commits the playbook to GitHub with the ticket number
6. 🏓 Tests device reachability before touching anything
7. ✅ Requests final human approval before pushing any config
8. ⚙️ Executes the change via Ansible AWX
9. 🔍 Verifies the change is live
10. 🎫 Closes the ticket — or rolls back and alerts the team on failure

> **No config is ever pushed without explicit human approval. No credentials are ever hardcoded. Every action is logged in ServiceNow and Slack.**

---

## Architecture

```
ServiceNow Ticket
       │
       ▼
┌─────────────────┐
│  AGENT 1        │  ── Reads ticket, extracts intent, checks compliance
│  PLANNER        │  ── Slack approval (Gate 1)
└────────┬────────┘
         │ Structured JSON Task
         ▼
┌─────────────────┐
│  AGENT 2        │  ── Queries RAG for device-specific Ansible syntax
│  CODER          │  ── Generates playbook with Vault variable refs
└────────┬────────┘  ── Commits to GitHub
         │
         ▼
┌─────────────────┐
│  AGENT 3        │  ── ICMP ping + SSH reachability pre-checks
│  VALIDATOR      │  ── Slack approval (Gate 2)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AGENT 4        │  ── Triggers AWX job, runs playbook
│  EXECUTOR +     │  ── Post-checks: ICMP + TCP port connectivity
│  POST-VALIDATOR │  ── Closes ticket or rollback + alert
└─────────────────┘
```

**Orchestration:** LangGraph stateful multi-agent graph with human-in-the-loop interrupt support

---

## The Four AI Agents

### Agent 1 — Planner
Reads the ServiceNow ticket and extracts: device name, IP address, device type, port, protocol, and direction. Validates the request against compliance policies using a RAG knowledge base. Sends an interactive Slack message to the network lead with **Approve** and **Reject** buttons. On approval, passes a structured JSON task downstream. On rejection, updates the ticket and stops.

### Agent 2 — Coder
Receives the structured task. Queries the RAG knowledge base for the correct Ansible syntax for the specific device type. Generates a complete, production-ready Ansible playbook using **Ansible Vault variable references** for all credentials — never hardcoded values. Commits the playbook to GitHub with the ticket number in the commit message.

### Agent 3 — Validator
Before any config is pushed, triggers an Ansible AWX job that runs two pre-checks against the target device:
- **ICMP ping** — confirms device is reachable
- **SSH connection test** — confirms device is manageable

If both pass, sends a second Slack approval message. If either fails, notifies the engineer with diagnostic details and stops the pipeline.

### Agent 4 — Executor + Post-Validator
On human approval, triggers the AWX job that runs the Ansible playbook against the device. After execution, runs two post-checks:
- **ICMP ping** — confirms device still reachable
- **TCP port connectivity test** — confirms the change is actually live

If post-checks pass, closes the ServiceNow ticket and posts a success summary to Slack. If post-checks fail, triggers a rollback playbook, updates the ticket with the failure reason, and alerts the team.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Orchestration** | LangGraph (stateful multi-agent graph with human-in-the-loop interrupt support) |
| **LLM** | Claude 3.5 Sonnet via Anthropic API (`temperature=0` for all agent calls) |
| **ITSM** | ServiceNow Developer Instance (REST API — read, update, close tickets) |
| **Automation** | Ansible AWX running in Docker (REST API — trigger job templates, poll results) |
| **Version Control** | GitHub (auto-commit all generated playbooks) |
| **Human Approvals** | Slack Block Kit (interactive Approve/Reject buttons, webhook callbacks resume the pipeline) |
| **Knowledge Base** | LlamaIndex + ChromaDB (local vector database with Cisco, Palo Alto, Juniper docs, runbooks, compliance policies) |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` (runs locally, zero API cost) |
| **Network Lab** | GNS3 with Cisco IOS images (responds to ICMP, SSH, Telnet — no real hardware needed) |
| **Secrets** | Ansible Vault (all credentials encrypted — vault variables only in every playbook) |
| **Webhook Server** | FastAPI (receives Slack button callbacks and resumes the paused pipeline) |

---

## Human Approval Gates

This pipeline enforces **two mandatory human approval gates** — neither can be bypassed.

```
Gate 1 ──── After compliance check, BEFORE playbook generation
            Network lead approves or rejects the change request via Slack

Gate 2 ──── After pre-checks pass, BEFORE any config is pushed
            Engineer approves or rejects the actual execution via Slack
```

- Both gates are **interactive Slack messages** with Approve / Reject buttons
- The pipeline **pauses and waits** — it does not poll
- It resumes **only when a human clicks** Approve or Reject
- Webhook callbacks are handled by the FastAPI server, which maps `ticket_number → LangGraph thread_id`

---

## Security Rules

These rules are **non-negotiable** and enforced from day one:

- 🔐 **Zero hardcoded credentials** anywhere in the codebase
- 🔒 All device credentials stored in **Ansible Vault** encrypted files
- 🗝️ All API keys stored in a **`.env` file** that is never committed
- 🚫 `.env` and `vault/` are always in **`.gitignore`**
- 🔍 **GitHub pre-commit hook** scans for accidental secret exposure before every push (`detect-secrets`)

---

## Project Structure

```
Agentic NetOps/
├── knowledge_base/
├── playbooks/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── coder.py
│   │   ├── executor.py
│   │   ├── planner.py
│   │   └── validator.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── nodes.py
│   │   ├── orchestrator.py
│   │   └── state.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── awx.py
│   │   ├── github_client.py
│   │   ├── servicenow.py
│   │   └── slack.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   │   ├── query.py
│   │   └── store.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── vault.py
│   ├── webhook/
│   │   ├── __init__.py
│   │   └── server.py
│   ├── config.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_config.py
│   ├── test_planner_live.py
│   └── test_rag.py
├── vault/
│   ├── README.md
│   └── credentials.yml.example    
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.10 or 3.11
- Git
- Docker (for Ansible AWX)
- GNS3 (for network lab simulation)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/agentic-netops.git
cd agentic-netops
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env       # Windows
cp .env.example .env         # macOS / Linux
```

Open `.env` and fill in your values:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
GITHUB_TOKEN=ghp_your-token-here
SLACK_BOT_TOKEN=xoxb-your-token-here
SERVICENOW_INSTANCE=https://yourinstance.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=your-password
AWX_HOST=http://localhost:8052
AWX_TOKEN=your-awx-token
```

### 5. Build the RAG knowledge base

```bash
python -m src.rag.ingest
```

Expected output:
```
📚 Knowledge Base Ingestion
  ✓ Loaded 9 documents
  ✓ Created 63 chunks
  ✓ Computed 63 embeddings
  ✓ 63 chunks in vector store
  ✅ Ingestion complete
```

### 6. Verify the RAG is working

```bash
python -c "from src.rag.query import query_knowledge_base; print(query_knowledge_base('What ports are allowed on Cisco firewalls?'))"
```

This should return relevant text from your compliance policy documents.

### 7. Run the test suite

```bash
python -m pytest tests/ -v
```

All 15 tests should pass.

---

## RAG Knowledge Base

The knowledge base is pre-loaded with 9 documents across 3 categories:

| Category | Contents |
|----------|----------|
| **Compliance Policies** | Allowed/blocked ports, change management rules, security baselines |
| **Device Runbooks** | Cisco IOS, Cisco ASA, Palo Alto, Juniper step-by-step guides |
| **Ansible References** | Module docs for `ios_config`, `panos_security_rule`, `junos_config` |

The **Planner Agent** queries compliance policies to validate change requests. The **Coder Agent** queries device runbooks and Ansible references to generate accurate playbooks.

### Vault Variable Naming Convention

All generated playbooks use these exact Ansible Vault variable names. **Do not change these** — they must be consistent across the entire project:

```yaml
vault_device_username
vault_device_password
vault_enable_password
```

---

## Build Timeline

| Phase | Timeline | Status |
|-------|----------|--------|
| Environment setup + RAG knowledge base | Week 1–2 | ✅ Complete |
| Build and test all four agents individually | Week 3–4 | 🔄 In Progress |
| ServiceNow + GitHub integration | Week 5–6 | ⏳ Pending |
| Ansible AWX + GNS3 lab setup | Week 7–8 | ⏳ Pending |
| End-to-end pipeline testing in lab | Week 9–10 | ⏳ Pending |
| Pilot with real low-risk changes | Week 11–12 | ⏳ Pending |
| Full production rollout | Week 13+ | ⏳ Pending |

---

## Current Status

**Week 1–2 — ✅ Fully Complete and Verified**

All four verification checks passed:

| Check | Result |
|-------|--------|
| All packages installed | ✅ Passed |
| All agent imports clean | ✅ Passed |
| RAG ingestion — 63 chunks in ChromaDB | ✅ Passed |
| RAG query returns correct results | ✅ Passed |
| All 15 tests passing | ✅ 15/15 |

**Next:** Week 3–4 — Building and testing the Planner Agent with live Claude API calls against the ChromaDB knowledge base.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/agent-improvement`
3. Never commit `.env`, `vault/`, or `chroma_db/` — these are gitignored
4. Run `pre-commit run --all-files` before pushing to ensure no secrets are exposed
5. Ensure all tests pass: `python -m pytest tests/ -v`
6. Open a pull request with a clear description of the change

---

## License

This project is for educational and enterprise demonstration purposes.

---

*Built with [LangGraph](https://github.com/langchain-ai/langgraph) · [Claude](https://anthropic.com) · [Ansible AWX](https://github.com/ansible/awx) · [ChromaDB](https://github.com/chroma-core/chroma)*


>>>>>>> 0101ffc4ff9abafd883e97d424d53e508e7f0008
