# Change Management Policy

## Purpose
This policy defines the requirements and procedures for all network configuration changes processed through the Agentic NetOps automation pipeline.

## Change Categories

### Standard Change
- Pre-approved, low-risk changes that follow a documented procedure.
- Examples: Opening pre-approved ports (80, 443), adding a new VLAN on an access switch.
- Approval: Single approval from the network team lead (Gate 1 only).

### Normal Change
- Changes that require assessment and planning before implementation.
- Examples: Modifying ACL rules, changing routing protocols, updating firewall policies.
- Approval: Dual approval — network team lead (Gate 1) + engineer review (Gate 2).

### Emergency Change
- Changes required to resolve a critical incident or security vulnerability.
- Examples: Blocking a compromised IP, opening emergency access for incident response.
- Approval: Can bypass Gate 1 with CISO verbal approval, but Gate 2 (pre-execution validation) is always mandatory.

## Change Request Requirements

Every change request must include:

1. **Target Device**: The specific device name and IP address.
2. **Device Type**: The platform (Cisco IOS, Palo Alto PAN-OS, Juniper Junos).
3. **Change Description**: Clear, unambiguous description of what needs to change.
4. **Business Justification**: Why this change is needed and what service it supports.
5. **Risk Assessment**: Potential impact if the change fails or causes an outage.
6. **Rollback Plan**: How to reverse the change if something goes wrong.
7. **Testing Plan**: How the change will be validated after implementation.

## Pre-Implementation Checks

Before any configuration change is pushed, the following checks are mandatory:

1. **Device Reachability (ICMP Ping)**: The target device must respond to ping from the management network.
2. **Management Access (SSH)**: An SSH connection must be successfully established.
3. **Configuration Backup**: A backup of the current running configuration must be saved before any change.

## Post-Implementation Checks

After a change is pushed, the following validations are required:

1. **Device Reachability (ICMP Ping)**: Confirm the device is still reachable.
2. **Service Verification**: Confirm the changed port/service is functioning (TCP connectivity test).
3. **No Collateral Damage**: Verify that existing services are not disrupted.

## Rollback Policy

- If any post-check fails, an automatic rollback must be triggered immediately.
- The rollback must restore the previous running configuration.
- After rollback, the ServiceNow ticket must be updated with the failure reason.
- The network team must be notified via Slack within 5 minutes of a rollback.
