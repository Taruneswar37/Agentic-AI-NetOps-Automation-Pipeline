"""
Agentic NetOps — Ansible Vault Helpers
Utilities for generating Ansible Vault variable references in playbooks.
"""

from __future__ import annotations


# ── Standard vault variable names ──
VAULT_VARS = {
    "username": "{{ vault_device_username }}",
    "password": "{{ vault_device_password }}",
    "enable_password": "{{ vault_enable_password }}",
    "snmp_ro": "{{ vault_snmp_ro_community }}",
    "snmp_rw": "{{ vault_snmp_rw_community }}",
}


def get_vault_ref(credential_name: str) -> str:
    """
    Return the Ansible Vault variable reference for a credential.

    Args:
        credential_name: One of 'username', 'password', 'enable_password',
                         'snmp_ro', 'snmp_rw'.

    Returns:
        Jinja2 variable reference string, e.g. '{{ vault_device_username }}'.

    Raises:
        ValueError: If the credential name is not recognized.
    """
    if credential_name not in VAULT_VARS:
        raise ValueError(
            f"Unknown credential '{credential_name}'. "
            f"Valid names: {list(VAULT_VARS.keys())}"
        )
    return VAULT_VARS[credential_name]


def build_vault_vars_block() -> dict[str, str]:
    """
    Return a dict suitable for inclusion in an Ansible playbook 'vars' section.

    Returns:
        Dict mapping human-readable names to vault variable references.

    Example output:
        {
            "ansible_user": "{{ vault_device_username }}",
            "ansible_password": "{{ vault_device_password }}",
            "ansible_become_password": "{{ vault_enable_password }}",
        }
    """
    return {
        "ansible_user": VAULT_VARS["username"],
        "ansible_password": VAULT_VARS["password"],
        "ansible_become_password": VAULT_VARS["enable_password"],
    }
