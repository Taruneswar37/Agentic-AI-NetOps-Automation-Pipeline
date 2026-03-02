"""
Tests for the RAG knowledge base — ingestion and query.
"""

import os
from pathlib import Path

import pytest


@pytest.fixture
def sample_knowledge_dir(tmp_path):
    """Create a temporary knowledge base with sample docs."""
    # Create compliance policy
    compliance_dir = tmp_path / "compliance_policies"
    compliance_dir.mkdir()
    (compliance_dir / "test_policy.md").write_text(
        "# Test Firewall Policy\n\n"
        "Port 443 (HTTPS) is allowed inbound on all perimeter firewalls.\n"
        "Port 22 (SSH) is allowed for management access only.\n"
        "Port 23 (Telnet) is PROHIBITED — use SSH instead.\n"
        "Port 3389 (RDP) must only be accessible via VPN.\n"
    )

    # Create runbook
    runbook_dir = tmp_path / "runbooks"
    runbook_dir.mkdir()
    (runbook_dir / "test_runbook.md").write_text(
        "# Cisco IOS Runbook\n\n"
        "To open port 443 on a Cisco IOS device:\n"
        "1. Enter enable mode\n"
        "2. Enter configure terminal\n"
        "3. Modify the ACL: ip access-list extended OUTSIDE-IN\n"
        "4. Add rule: permit tcp any any eq 443\n"
        "5. Exit and save: write memory\n"
    )

    # Create Ansible reference
    ansible_dir = tmp_path / "ansible_references"
    ansible_dir.mkdir()
    (ansible_dir / "test_ansible.md").write_text(
        "# Cisco IOS Ansible Modules\n\n"
        "Use cisco.ios.ios_acls for ACL management.\n"
        "Connection: ansible_network_os: cisco.ios.ios\n"
        "Connection type: ansible.netcommon.network_cli\n"
        "Always use vault variables for credentials.\n"
    )

    return tmp_path


def test_load_documents(sample_knowledge_dir):
    """Documents should load from the knowledge base directory."""
    from src.rag.ingest import load_documents

    docs = load_documents(sample_knowledge_dir)
    assert len(docs) == 3
    categories = {d["category"] for d in docs}
    assert "compliance_policies" in categories
    assert "runbooks" in categories
    assert "ansible_references" in categories


def test_chunk_text():
    """Text should be chunked with overlap."""
    from src.rag.ingest import chunk_text

    text = "A" * 1000
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 1
    # Each chunk should be ≤ 200 chars
    for chunk in chunks:
        assert len(chunk) <= 200


def test_chunk_overlap():
    """Consecutive chunks should overlap."""
    from src.rag.ingest import chunk_text

    text = "ABCDEFGHIJ" * 100  # 1000 chars
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    # The last 50 chars of chunk[0] should be in the first 50 chars of chunk[1]
    if len(chunks) > 1:
        assert chunks[0][-50:] == chunks[1][:50]


def test_generate_chunk_id():
    """Chunk IDs should be deterministic and unique."""
    from src.rag.ingest import generate_chunk_id

    id1 = generate_chunk_id("test.md", 0)
    id2 = generate_chunk_id("test.md", 1)
    id3 = generate_chunk_id("test.md", 0)  # Same as id1

    assert id1 != id2
    assert id1 == id3
    assert len(id1) == 16


def test_vault_helpers():
    """Vault helpers should return proper Jinja2 references."""
    from src.utils.vault import get_vault_ref, build_vault_vars_block

    assert get_vault_ref("username") == "{{ vault_device_username }}"
    assert get_vault_ref("password") == "{{ vault_device_password }}"
    assert "{{" in get_vault_ref("enable_password")

    block = build_vault_vars_block()
    assert "vault_device_username" in block["ansible_user"]
    assert "vault_device_password" in block["ansible_password"]

    with pytest.raises(ValueError):
        get_vault_ref("invalid_name")
