# Firewall Rule Change Policy

## Scope
This policy governs all firewall rule changes across the enterprise network, including perimeter firewalls, internal segmentation firewalls, and cloud security groups.

## Allowed Ports — Inbound

The following ports are pre-approved for inbound access on perimeter firewalls when a valid business justification is provided:

| Port | Protocol | Service | Risk Level |
|------|----------|---------|------------|
| 22   | TCP      | SSH     | Medium     |
| 80   | TCP      | HTTP    | Low        |
| 443  | TCP      | HTTPS   | Low        |
| 8443 | TCP      | Alt HTTPS | Low     |

## Allowed Ports — Outbound

Outbound access is generally permitted to the following ports:

| Port | Protocol | Service | Risk Level |
|------|----------|---------|------------|
| 53   | TCP/UDP  | DNS     | Low        |
| 80   | TCP      | HTTP    | Low        |
| 123  | UDP      | NTP     | Low        |
| 443  | TCP      | HTTPS   | Low        |

## Prohibited Ports

The following ports must NEVER be opened on perimeter firewalls under any circumstances:

| Port | Protocol | Service | Reason |
|------|----------|---------|--------|
| 23   | TCP      | Telnet  | Unencrypted protocol — use SSH instead |
| 21   | TCP      | FTP     | Unencrypted protocol — use SFTP instead |
| 3389 | TCP      | RDP     | Must only be accessible via VPN |
| 1433 | TCP      | MSSQL   | Database ports must never face the internet |
| 3306 | TCP      | MySQL   | Database ports must never face the internet |
| 5432 | TCP      | PostgreSQL | Database ports must never face the internet |
| 6379 | TCP      | Redis   | Must be internal only |
| 27017| TCP      | MongoDB | Must be internal only |

## Compliance Rules

1. **Business Justification Required**: Every firewall rule change must have a documented business justification linked to a ServiceNow change request.

2. **Least Privilege**: Rules must be as specific as possible — no "any-to-any" or "0.0.0.0/0" source rules unless explicitly approved by the CISO.

3. **Time-Limited Access**: Temporary access rules must have an expiration date. Rules older than 90 days without renewal must be reviewed.

4. **Dual Approval**: All changes to perimeter firewall rules require approval from both the requesting team lead and the network security team.

5. **Change Window**: Firewall changes on production devices must be executed during the approved maintenance window (Saturday 02:00–06:00 UTC) unless classified as an emergency.

6. **Rollback Plan**: Every change must have a documented rollback procedure. Automated rollback is mandatory for all changes pushed via the automation pipeline.

7. **Post-Change Verification**: All changes must be verified within 30 minutes of implementation. Verification must include connectivity testing for the affected ports.
