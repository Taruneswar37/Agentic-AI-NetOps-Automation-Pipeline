# Cisco IOS — Ansible Module Reference

## Collection
`cisco.ios` — Official Ansible collection for Cisco IOS/IOS-XE devices.

Install: `ansible-galaxy collection install cisco.ios`

## Connection Settings

Every playbook targeting Cisco IOS must include these connection variables:

```yaml
vars:
  ansible_network_os: cisco.ios.ios
  ansible_connection: ansible.netcommon.network_cli
  ansible_user: "{{ vault_device_username }}"
  ansible_password: "{{ vault_device_password }}"
  ansible_become: true
  ansible_become_method: enable
  ansible_become_password: "{{ vault_enable_password }}"
```

## Key Modules

### cisco.ios.ios_acls — ACL Management

Manage Access Control Lists declaratively.

```yaml
- name: Add HTTPS permit rule to ACL
  cisco.ios.ios_acls:
    config:
      - afi: ipv4
        acls:
          - name: OUTSIDE-IN
            aces:
              - grant: permit
                protocol: tcp
                source:
                  any: true
                destination:
                  any: true
                  port_protocol:
                    eq: "443"
                sequence: 110
    state: merged
```

**States:**
- `merged` — Adds rules without removing existing ones (recommended for additions)
- `replaced` — Replaces the entire ACL with the specified rules
- `deleted` — Removes specified rules
- `overridden` — Overrides all ACLs on the device

### cisco.ios.ios_config — Raw Configuration

Send raw IOS configuration lines. Use this for operations not covered by resource modules.

```yaml
- name: Open port 8443
  cisco.ios.ios_config:
    lines:
      - permit tcp any any eq 8443
    parents:
      - ip access-list extended OUTSIDE-IN
    save_when: modified
```

### cisco.ios.ios_ping — ICMP Ping

```yaml
- name: Ping target device
  cisco.ios.ios_ping:
    dest: "{{ target_host }}"
    count: 5
  register: ping_result

- name: Report ping result
  debug:
    msg: "ICMP_PING: {{ 'OK' if ping_result.packet_loss == '0%' else 'FAILED' }}"
```

### cisco.ios.ios_facts — Gather Device Facts

```yaml
- name: Gather IOS facts
  cisco.ios.ios_facts:
    gather_subset:
      - config
      - interfaces
```

## Complete Playbook Example — Open Port 443

```yaml
---
# Ticket: CHG0012345
# Action: Open port 443 (TCP, inbound) on Firewall-NYC-01
- name: Open HTTPS on Cisco IOS Firewall
  hosts: "{{ target_host }}"
  gather_facts: false
  vars:
    ansible_network_os: cisco.ios.ios
    ansible_connection: ansible.netcommon.network_cli
    ansible_user: "{{ vault_device_username }}"
    ansible_password: "{{ vault_device_password }}"
    ansible_become: true
    ansible_become_method: enable
    ansible_become_password: "{{ vault_enable_password }}"

  tasks:
    - name: Add HTTPS permit rule
      cisco.ios.ios_acls:
        config:
          - afi: ipv4
            acls:
              - name: OUTSIDE-IN
                aces:
                  - grant: permit
                    protocol: tcp
                    source:
                      any: true
                    destination:
                      any: true
                      port_protocol:
                        eq: "443"
                    sequence: 110
        state: merged

    - name: Save configuration
      cisco.ios.ios_config:
        save_when: always
```
