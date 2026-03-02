# Security Baseline Standards

## Device Hardening Baseline

All network devices managed by the Agentic NetOps pipeline must meet the following security baseline before any change is authorized.

### Authentication & Access Control

1. **SSH Only**: All devices must use SSH (version 2) for management access. Telnet must be disabled.
2. **Local Authentication**: Devices must have a local fallback admin account with a strong password (16+ characters, mixed case, numbers, symbols).
3. **TACACS+/RADIUS**: AAA authentication against a central TACACS+ or RADIUS server must be configured.
4. **Session Timeout**: Management sessions must timeout after 10 minutes of inactivity.
5. **Login Banner**: All devices must display an authorized access warning banner.

### Logging & Monitoring

1. **Syslog**: All devices must send syslog messages to the central SIEM (severity level: informational and above).
2. **NTP Sync**: All devices must synchronize time with the corporate NTP servers. Time accuracy is critical for log correlation.
3. **SNMP**: If enabled, SNMP must use version 3 with authentication and encryption. SNMP v1/v2c must be disabled.
4. **Change Logging**: All configuration changes must be logged with a timestamp, username, and source IP.

### Network Security

1. **ACL Standards**: Access control lists must follow the "deny by default, permit by exception" model.
2. **Anti-Spoofing**: Ingress filtering (uRPF or ACLs) must be enabled on all edge interfaces.
3. **Control Plane Protection**: CoPP (Control Plane Policing) must be configured to protect the device management plane.
4. **Unused Interfaces**: All unused physical interfaces must be administratively shut down and placed in an unused VLAN.

### Encryption

1. **Encrypted Passwords**: All passwords stored on device must use Type 8 or Type 9 encryption (Cisco), or equivalent.
2. **VPN Standards**: For site-to-site VPNs, use IKEv2 with AES-256-GCM encryption and SHA-384 integrity.
3. **TLS**: Any web management interfaces must enforce TLS 1.2 or higher.

## Compliance Verification

Devices are audited quarterly. Non-compliant devices are flagged and must be remediated within 14 days. Changes to non-compliant devices via the automation pipeline will be blocked until compliance is restored.
