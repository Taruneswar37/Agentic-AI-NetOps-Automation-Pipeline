# Palo Alto PAN-OS Firewall — Operations Runbook

## Device Overview
- **Platform**: Palo Alto Networks PAN-OS
- **Management Protocol**: SSH (port 22), HTTPS API (port 443)
- **CLI Access**: Configure mode only available via SSH; REST API preferred for automation.
- **ansible_network_os**: N/A (uses `paloaltonetworks.panos` collection with API)
- **Connection Type**: `httpapi` (via PAN-OS XML API)

## Common Operations

### Opening a Port (Security Policy)

On PAN-OS, firewall rules are called "security policies." To allow traffic on a specific port, you create or modify a security policy.

**Manual CLI Steps:**
```
configure
set rulebase security rules Allow-HTTPS-Inbound from untrust to trust source any destination any application ssl service service-https action allow
commit
```

**Using the PAN-OS API:**
```
curl -k -X POST "https://<firewall>/api/?type=config&action=set&xpath=/config/devices/entry/vsys/entry/rulebase/security/rules/entry[@name='Allow-HTTPS']&element=<source><member>any</member></source><destination><member>any</member></destination><service><member>service-https</member></service><action>allow</action>" -d "key=<api_key>"
```

**Key Points:**
- PAN-OS uses named services (e.g., `service-https` for port 443/TCP).
- Custom services can be created for non-standard ports.
- All changes require a `commit` to take effect on the data plane.
- PAN-OS supports commit validation (`commit validate`) before actual commit.

### Creating a Custom Service Object

```
configure
set service custom-port-8443 protocol tcp port 8443
commit
```

### Viewing Security Policies

```
show running security-policy
show system info
```

## Pre-Check Commands

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Reachability | `ping host <device_ip>` | Received replies |
| SSH Access | `ssh admin@<device_ip>` | Successful login |
| Commit Status | `show jobs all` | No pending commits |

## Post-Check Commands

| Check | Command | Expected Result |
|-------|---------|-----------------|
| Policy Active | `show running security-policy` | New rule visible |
| Traffic Log | `show log traffic` | Sessions matching new rule |
| System Health | `show system resources` | No resource exhaustion |

## Rollback Procedure

PAN-OS maintains a configuration audit trail. To rollback:

1. List available configs:
   ```
   show config audit
   ```
2. Load previous configuration:
   ```
   load config version <N>
   ```
3. Commit the rollback:
   ```
   commit
   ```

## Troubleshooting

- **Rule not matching traffic**: Check zone assignment — PAN-OS policies are zone-based, not interface-based.
- **Commit failed**: Run `show jobs all` and `show config audit` for details.
- **API timeout**: Verify HTTPS management is enabled on the correct interface.
