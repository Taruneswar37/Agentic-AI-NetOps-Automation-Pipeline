# Ansible Vault — Encrypted Credentials

This directory stores Ansible Vault encrypted credential files.

## Usage

### Encrypt a file
```bash
ansible-vault encrypt vault/credentials.yml
```

### Decrypt a file (for editing)
```bash
ansible-vault edit vault/credentials.yml
```

### Use in playbooks
Reference vault variables in your playbooks:
```yaml
vars:
  ansible_user: "{{ vault_device_username }}"
  ansible_password: "{{ vault_device_password }}"
```

## ⚠️ Security

- **NEVER** commit unencrypted vault files
- The `.gitignore` excludes all `.yml` files in this directory except the example
- Store the vault password in your `.env` file as `ANSIBLE_VAULT_PASSWORD`
