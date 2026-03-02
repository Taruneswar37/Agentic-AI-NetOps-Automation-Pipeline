# Cisco IOS Firewall — Operations Runbook

## Device Overview
- **Platform**: Cisco IOS / IOS-XE
- **Management Protocol**: SSH (port 22)
- **CLI Access**: Enable mode → configure terminal
- **ansible_network_os**: `cisco.ios.ios`
- **Connection Type**: `network_cli`

## Common Operations

### Opening a Port (ACL Modification)

To open a specific port on a Cisco IOS device, you modify the relevant extended ACL.

**Manual CLI Steps:**
```
enable
configure terminal
ip access-list extended OUTSIDE-IN
  permit tcp any any eq 443
  exit
exit
write memory
```

**Key Points:**
- Always specify the ACL name (e.g., `OUTSIDE-IN`) — never use numbered ACLs.
- Use `write memory` to persist changes across reboots.
- Verify with `show access-lists OUTSIDE-IN`.

### Closing a Port

```
enable
configure terminal
ip access-list extended OUTSIDE-IN
  no permit tcp any any eq 23
  exit
exit
write memory
```

### Viewing Current ACL Rules

```
show access-lists OUTSIDE-IN
show ip access-lists
```

### Backup Running Configuration

```
copy running-config startup-config
show running-config
```

## Pre-Check Commands

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Reachability | `ping <device_ip>` | 5/5 packets received |
| SSH Access | `ssh -l admin <device_ip>` | Successful login |
| Interface Status | `show ip interface brief` | Relevant interfaces UP/UP |

## Post-Check Commands

| Check | Command | Expected Result |
|-------|---------|-----------------|
| ACL Applied | `show access-lists <acl_name>` | New rule visible |
| Traffic Flowing | `telnet <device_ip> <port>` | Connection established (or refused, not timeout) |
| No Errors | `show logging | tail 20` | No error messages related to the change |

## Rollback Procedure

1. Revert to the previous configuration:
   ```
   configure replace flash:backup-config force
   ```
2. Alternatively, manually remove the added rule:
   ```
   ip access-list extended OUTSIDE-IN
     no permit tcp any any eq <port>
   ```
3. Save the rollback:
   ```
   write memory
   ```

## Troubleshooting

- **ACL not taking effect**: Ensure the ACL is applied to the correct interface and direction with `show ip interface <intf>`.
- **SSH connection refused**: Check `line vty 0 15` settings and `transport input ssh`.
- **Changes lost after reboot**: Always run `write memory` after changes.
