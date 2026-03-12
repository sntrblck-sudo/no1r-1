HEAL AUTOMATION — Threat Model (concise)

Scope: the wrapper script /usr/local/bin/no1r_heal_gateway.sh plus a narrow sudoers entry permitting a dedicated system user to run that wrapper as root.

Assets of value
- Availability of openclaw-gateway (service restarts could be abused to degrade or mask events)
- Integrity of wrapper script and sudoers file
- Audit trails (logs, core/history entries)

Threat actors
- Local privileged user with write access (intentional or accidental misconfiguration)
- Remote attacker who gains local file-write or command execution on the host
- Malicious insider who can edit the wrapper or sudoers

Attack vectors & mitigations
1) Wrapper tampering
   - Risk: attacker modifies wrapper to run arbitrary commands as root.
   - Mitigations: wrapper owned by root, mode 750; check wrapper checksum before each run (sentinel can verify); keep wrapper under version control; restrict who can write to repo and host.

2) Sudoers misconfiguration
   - Risk: overly broad sudo rule grants more than intended.
   - Mitigations: use explicit wrapper path in sudoers; avoid allowing general systemctl; visudo syntax checks; code review before applying.

3) Repeated or automated restarts (availability abuse)
   - Risk: scripted restarts cause service thrashing.
   - Mitigations: rate-limit in wrapper (current: 300s cap); backoff and exponential delay on repeated failures; disable flag (/etc/no1r/heal_disabled) and operator override.

4) Log tampering / cover-up
   - Risk: attacker removes evidence of abuse.
   - Mitigations: centralize logs (push alerts off-host), push copies of /var/log/no1r_heal.log into git-locked audit storage or remote logging, sign/commit audit entries to core/history.

5) Unauthorized elevation of messages
   - Risk: worker bodies craft malicious public posts that appear endorsed.
   - Mitigations: elevation messages must be reviewed by no1r-1; require audit_reference; keep a mandatory delay/confirmation step for public posts.

Operational controls (procedures)
- Code review before applying sudoers and wrapper changes.  
- Post‑install audit: visudo -c, run test restart, and append history.  
- Monitoring: alert on rate-limit hits, repeated heal failures, sudden increases in elevation frequency.

Residual risk
- Any sudo path adds risk. Keep scope minimal and require operator approval for broader privilege changes.
