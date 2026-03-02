# Juniper Junos Firewall — Operations Runbook

## Device Overview
- **Platform**: Juniper Junos OS (SRX Series)
- **Management Protocol**: SSH (port 22), NETCONF (port 830)
- **CLI Access**: Operational mode → configure mode
- **ansible_network_os**: `junipernetworks.junos.junos`
- **Connection Type**: `netconf` (preferred) or `network_cli`

## Common Operations

### Opening a Port (Firewall Filter)

Junos uses firewall filters (similar to ACLs) and security policies (on SRX). For SRX series:

**Security Policy (SRX):**
```
configure
set security policies from-zone untrust to-zone trust policy allow-https-in match source-address any destination-address any application junos-https
set security policies from-zone untrust to-zone trust policy allow-https-in then permit
commit
```

**Firewall Filter (EX/MX/QFX):**
```
configure
set firewall family inet filter OUTSIDE-IN term allow-https from protocol tcp destination-port 443
set firewall family inet filter OUTSIDE-IN term allow-https then accept
commit
```

**Key Points:**
- Junos uses a candidate configuration model — changes are staged and only applied on `commit`.
- Use `commit confirmed 5` for safety — auto-rollback after 5 minutes if not confirmed.
- Use `show | compare` to review pending changes before committing.
- SRX devices use zone-based security policies; EX/MX/QFX use firewall filters.

### Closing a Port

```
configure
delete security policies from-zone untrust to-zone trust policy allow-telnet-in
commit
```

### Viewing Policies/Filters

```
show security policies
show firewall filter OUTSIDE-IN
show configuration firewall
```

## Pre-Check Commands

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Reachability | `ping <device_ip> count 5` | 5/5 packets received |
| SSH Access | `ssh admin@<device_ip>` | Successful login |
| NETCONF | `ssh admin@<device_ip> -s netconf` | NETCONF hello message |
| Uncommitted Changes | `show | compare` | No output (clean state) |

## Post-Check Commands

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Policy Active | `show security policies` | New policy visible |
| Traffic Flowing | `show security flow session destination-port <port>` | Active sessions |
| System Health | `show system alarms` | No active alarms |

## Rollback Procedure

Junos maintains the last 50 configurations. To rollback:

1. View available rollbacks:
   ```
   show system rollback compare 0 1
   ```
2. Rollback to previous config:
   ```
   configure
   rollback 1
   commit
   ```
3. For immediate rollback during risky changes, use:
   ```
   commit confirmed 5
   ```
   This auto-reverts in 5 minutes unless you run `commit` again to confirm.

## Troubleshooting

- **Policy not matching**: Verify zone assignments with `show security zones`.
- **Commit errors**: Check with `commit check` before committing.
- **NETCONF not working**: Ensure `set system services netconf ssh` is configured.
- **Candidate config locked**: Another user may be in configure mode — check with `show system users`.
