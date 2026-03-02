# Juniper Junos — Ansible Module Reference

## Collection
`junipernetworks.junos` — Official Ansible collection for Juniper Junos OS devices.

Install: `ansible-galaxy collection install junipernetworks.junos`

## Connection Settings

Junos supports both `network_cli` (SSH) and `netconf` connections. NETCONF is preferred.

```yaml
vars:
  ansible_network_os: junipernetworks.junos.junos
  ansible_connection: ansible.netcommon.netconf
  ansible_user: "{{ vault_device_username }}"
  ansible_password: "{{ vault_device_password }}"
```

**For SSH CLI fallback:**
```yaml
vars:
  ansible_network_os: junipernetworks.junos.junos
  ansible_connection: ansible.netcommon.network_cli
  ansible_user: "{{ vault_device_username }}"
  ansible_password: "{{ vault_device_password }}"
```

## Key Modules

### junipernetworks.junos.junos_acls — ACL / Firewall Filter Management

```yaml
- name: Allow HTTPS inbound
  junipernetworks.junos.junos_acls:
    config:
      - afi: ipv4
        acls:
          - name: OUTSIDE-IN
            aces:
              - name: allow-https
                protocol: tcp
                destination:
                  port_protocol:
                    eq: "443"
                grant: permit
    state: merged
```

### junipernetworks.junos.junos_config — Raw Configuration

```yaml
- name: Add security policy for HTTPS
  junipernetworks.junos.junos_config:
    lines:
      - set security policies from-zone untrust to-zone trust policy allow-https match source-address any
      - set security policies from-zone untrust to-zone trust policy allow-https match destination-address any
      - set security policies from-zone untrust to-zone trust policy allow-https match application junos-https
      - set security policies from-zone untrust to-zone trust policy allow-https then permit
    confirm_commit: true
    comment: "Ticket CHG0012345 - Open HTTPS"
```

**Key Parameters:**
- `confirm_commit: true` — Uses `commit confirmed` for safety (auto-rollback if not confirmed).
- `comment` — Adds a commit comment for audit trail.

### junipernetworks.junos.junos_ping — ICMP Ping

```yaml
- name: Ping target device
  junipernetworks.junos.junos_ping:
    dest: "{{ target_host }}"
    count: 5
  register: ping_result

- name: Report ping result
  debug:
    msg: "ICMP_PING: {{ 'OK' if ping_result.packet_loss == '0%' else 'FAILED' }}"
```

### junipernetworks.junos.junos_facts — Gather Device Facts

```yaml
- name: Gather Junos facts
  junipernetworks.junos.junos_facts:
    gather_subset:
      - config
      - interfaces
```

## Complete Playbook Example — Open Port 443 (SRX)

```yaml
---
# Ticket: CHG0012345
# Action: Allow inbound HTTPS on Juniper SRX Firewall
- name: Open HTTPS on Juniper SRX
  hosts: "{{ target_host }}"
  gather_facts: false
  vars:
    ansible_network_os: junipernetworks.junos.junos
    ansible_connection: ansible.netcommon.netconf
    ansible_user: "{{ vault_device_username }}"
    ansible_password: "{{ vault_device_password }}"

  tasks:
    - name: Add HTTPS security policy
      junipernetworks.junos.junos_config:
        lines:
          - set security policies from-zone untrust to-zone trust policy allow-https-inbound match source-address any
          - set security policies from-zone untrust to-zone trust policy allow-https-inbound match destination-address any
          - set security policies from-zone untrust to-zone trust policy allow-https-inbound match application junos-https
          - set security policies from-zone untrust to-zone trust policy allow-https-inbound then permit
        confirm_commit: true
        comment: "CHG0012345 - Open HTTPS inbound"

    - name: Confirm the commit
      junipernetworks.junos.junos_config:
        confirm_commit: true
```

## Notes

- Junos uses a candidate configuration model. Changes are staged and applied on commit.
- Always use `confirm_commit: true` for safety — Junos will auto-rollback if not confirmed within the timeout.
- NETCONF (port 830) must be enabled on the device: `set system services netconf ssh`.
- For SRX devices, use security policies (zone-based). For EX/MX/QFX, use firewall filters.
