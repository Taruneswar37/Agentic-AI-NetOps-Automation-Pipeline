<<<<<<< HEAD
# 🚀 Agentic NetOps

**AI-Powered Network Operations Automation Pipeline.**

An enterprise-grade system that automates the full lifecycle of network change requests — from ServiceNow ticket submission to post-validation and closure — using a multi-agent AI architecture.

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   PLANNER    │────▶│    CODER     │────▶│  VALIDATOR   │────▶│   EXECUTOR   │
│              │     │              │     │              │     │              │
│ Parse ticket │     │ Gen playbook │     │ Pre-checks   │     │ Run playbook │
│ Compliance   │     │ Commit to GH │     │ Ping + SSH   │     │ Post-checks  │
│ Slack Gate 1 │     │              │     │ Slack Gate 2 │     │ Close/Rollback│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Human-in-the-loop**: Two mandatory approval gates via Slack interactive messages.

---

## Quick Start

### 1. Clone & Install

```bash
git clone <repo-url> && cd agentic-netops
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
```

### 2. Configure

```bash
copy .env.example .env
# Fill in your API keys and credentials in .env
```

### 3. Build the Knowledge Base

```bash
python src/rag/ingest.py
```

### 4. Start the Webhook Server

```bash
uvicorn src.webhook.server:app --host 0.0.0.0 --port 8000
```

### 5. Run the Pipeline

```bash
python src/main.py
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | LangGraph (stateful multi-agent graph) |
| LLM | Claude 3.5 Sonnet via Anthropic API |
| ITSM | ServiceNow (REST API) |
| Automation | Ansible AWX (Docker) |
| Version Control | GitHub (auto-commit playbooks) |
| Approvals | Slack Block Kit (interactive buttons) |
| Knowledge Base | LlamaIndex + ChromaDB |
| Network Lab | GNS3 with Cisco IOS images |
| Secrets | Ansible Vault + .env |
| Webhook Server | FastAPI |

---

## Security

- **Zero hardcoded credentials** — all secrets in `.env` or Ansible Vault
- **Pre-commit hooks** scan for accidental secret exposure
- `.env` and `vault/` are in `.gitignore`

---

## Project Structure

```
agentic-netops/
├── src/
│   ├── agents/          # Planner, Coder, Validator, Executor
│   ├── graph/           # LangGraph orchestrator
│   ├── integrations/    # ServiceNow, Slack, GitHub, AWX clients
│   ├── rag/             # LlamaIndex + ChromaDB pipeline
│   ├── webhook/         # FastAPI callback server
│   └── utils/           # Logging, vault helpers
├── knowledge_base/      # Source docs for RAG
├── playbooks/           # Generated Ansible playbooks
├── vault/               # Ansible Vault encrypted credentials
├── tests/               # Test suite
└── docker-compose.yml   # AWX stack
```
=======
# Agentic-AI-NetOps-Automation-Pipeline
>>>>>>> 037ba9599c6b0080feaac7296478cb755db5929d
