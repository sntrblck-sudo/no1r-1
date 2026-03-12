ALERT & ESCALATION TEMPLATES (Telegram-ready)

1) heal_attempt (auto success)
Subject: [no1r] Heal executed — openclaw-gateway restarted
Body: ts={timestamp} | summary={short summary} | result=success | report={audit_reference}
Action: No action required unless follow-up requested. (Click link for details.)

2) heal_failed (requires operator)
Subject: [URGENT no1r] Heal failed — operator action required
Body: ts={timestamp} | summary={short summary} | result=failed | error={short error} | report={audit_reference}
Action: Please review logs (/var/log/no1r_heal.log) and systemctl status. Consider manual restart or disable automatic heals.

3) elevation_requested (worker -> no1r-1)
Subject: [no1r-elevation] Proposed external post — review required
Body: ts={timestamp} | summary={1-line summary} | recommended_action={post/edit/reject} | confidence={low/med/high} | report={audit_reference}
Action: no1r-1 to review and either: post, edit+post, or reject+comment.

Formatting notes
- Keep messages short: subject <= 80 chars; body <= 2 lines.  
- Always include `audit_reference` as a file path or repo URL to the SimulationReport.  
- Set severity labels: info / warning / urgent.  

Example (heal_failed):
Subject: [URGENT no1r] Heal failed — operator action required
Body: ts=2026-03-12T11:45:55Z | summary=Gateway heal attempt failed (permission error) | result=failed | error=permission denied | report=<repo>/experiments/results/sentinel_...json
Action: Review logs and run: sudo systemctl status openclaw-gateway.service
