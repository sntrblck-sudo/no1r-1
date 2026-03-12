TELEMETRY & MONITORING CHECKLIST — Heal automation

Essential metrics / signals
- heal_attempts_total (counter) — increments each time wrapper is invoked
- heal_success_total / heal_failure_total (counters)
- heal_rate_limit_hits (counter)
- elevation_requests_total (counter) — worker elevation messages
- elevation_approval_rate (ratio) — approved / requested
- sudoers_file_mod_time (timestamp) — alert if changed unexpectedly
- rate_since_last_restart (time) — wrapper writes last-run timestamp to /var/run/no1r_heal_last

Alerts & thresholds (examples)
- heal_failure_total > 1 within 10 minutes → ALERT (operator)  
- heal_rate_limit_hits > 5 per hour → ALERT (investigate possible thrash)  
- elevation_requests_total spikes  > 10/day → REVIEW (possible automation abuse)  
- sudoers_file_mod_time changed outside change-window → URGENT (possible tampering)

Log signals
- Monitor /var/log/no1r_heal.log for: "heal failed", "rate-limited", "heal disabled"
- Push key log lines to central log store (or commit to an audit file inside core/history periodically).

Dashboards & widgets
- Simple single-panel view: heal_attempts, success_rate, rate-limit hits, last-heal timestamp.  
- Elevation dashboard: recent elevation summaries, approval decisions, and time-to-approve distribution.

Retention & audit
- Keep no1r_heal.log for at least 30 days locally and push monthly snapshots to core/history or remote logging.  
- Record every automated heal decision in core/history with timestamp, commit id, and the responsible sentinel PID.

Implementation note
- Start with local file alerts (cron or health_pulse daemon) and then integrate into your existing monitoring (Prometheus/Alertmanager, or simple Telegram alerts as per templates).
