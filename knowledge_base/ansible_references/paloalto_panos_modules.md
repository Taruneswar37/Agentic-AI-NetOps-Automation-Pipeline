# Palo Alto PAN-OS — Ansible Module Reference

## Collection
`paloaltonetworks.panos` — Official Ansible collection for Palo Alto Networks firewalls.

Install: `ansible-galaxy collection install paloaltonetworks.panos`

## Connection Settings

PAN-OS uses the HTTP API, not SSH CLI. Connection is handled via module parameters.

```yaml
vars:
  panos_provider:
    ip_address: "{{ target_host }}"
    username: "{{ vault_device_username }}"
    password: "{{ vault_device_password }}"
```

**Important:** PAN-OS Ansible modules do NOT use `ansible_connection: network_cli`. Instead, each module takes a `provider` parameter with the API credentials.

## Key Modules

### paloaltonetworks.panos.panos_security_rule — Security Policy Management

```yaml
- name: Allow HTTPS inbound
  paloaltonetworks.panos.panos_security_rule:
    provider: "{{ panos_provider }}"
    rule_name: "Allow-HTTPS-Inbound"
    source_zone: ["untrust"]
    destination_zone: ["trust"]
    source_ip: ["any"]
    destination_ip: ["any"]
    application: ["ssl"]
    service: ["service-https"]
    action: "allow"
    location: "bottom"
    commit: false
```

### paloaltonetworks.panos.panos_service_object — Custom Service Object

```yaml
- name: Create custom service for port 8443
  paloaltonetworks.panos.panos_service_object:
    provider: "{{ panos_provider }}"
    name: "service-custom-8443"
    protocol: "tcp"
    destination_port: "8443"
    description: "Custom HTTPS on port 8443"
    commit: false
```

### paloaltonetworks.panos.panos_commit — Commit Configuration

```yaml
- name: Commit changes to PAN-OS
  paloaltonetworks.panos.panos_commit:
    provider: "{{ panos_provider }}"
```

**Important:** PAN-OS changes are staged in the candidate configuration. They only take effect after a `commit`. Always include a commit task at the end.

### paloaltonetworks.panos.panos_op — Operational Commands

```yaml
- name: Run a ping from the firewall
  paloaltonetworks.panos.panos_op:
    provider: "{{ panos_provider }}"
    cmd: "<request><icmp><host>{{ target_host }}</host></icmp></request>"
  register: ping_result
```

## Complete Playbook Example — Open Port 443

```yaml
---
# Ticket: CHG0012345
# Action: Allow HTTPS inbound on PAN-OS Firewall
- name: Open HTTPS on Palo Alto Firewall
  hosts: localhost
  gather_facts: false
  connection: local
  vars:
    panos_provider:
      ip_address: "{{ target_host }}"
      username: "{{ vault_device_username }}"
      password: "{{ vault_device_password }}"

  tasks:
    - name: Create security rule for HTTPS
      paloaltonetworks.panos.panos_security_rule:
        provider: "{{ panos_provider }}"
        rule_name: "Allow-HTTPS-Inbound"
        source_zone: ["untrust"]
        destination_zone: ["trust"]
        source_ip: ["any"]
        destination_ip: ["any"]
        application: ["ssl"]
        service: ["service-https"]
        action: "allow"
        location: "bottom"
        commit: false

    - name: Commit configuration
      paloaltonetworks.panos.panos_commit:
        provider: "{{ panos_provider }}"
```

## Notes

- PAN-OS playbooks run against `localhost` with `connection: local` — the modules reach out to the firewall API directly.
- Always set `commit: false` on individual tasks and use a dedicated `panos_commit` task at the end.
- For high-availability (HA) pairs, commit to both peers using `panos_commit` with `device_group` or by running the commit on each device.
