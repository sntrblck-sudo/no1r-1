# OPS_POLICY

Minimal ops policy for `no1rlocal`.

This is what "OK" means operationally.

---

## Gateway

Gateway status is considered:

- **OK** when:
  - `openclaw status` reports Gateway `reachable` on local loopback, and
  - latency is < 200ms.

- **WARN/FAIL** when:
  - Gateway is unreachable, or
  - latency is consistently > 500ms for multiple checks, or
  - the Gateway service is stopped.

Immediate actions:

1. `openclaw status`
2. If stopped: `openclaw gateway start` or `sudo systemctl restart openclaw-gateway`

---

## Sentinel

Sentinel is considered:

- **OK** when:
  - `systemctl status sentinel` shows `active (running)`, and
  - `curl http://localhost:18799/health` returns `{ "status": "ok", ... }`.

- **WARN/FAIL** when:
  - the service is not running, or
  - `/health` does not return `status=ok`.

Immediate actions:

1. `sudo systemctl restart sentinel`
2. Check logs: `tail -40 ~/\.openclaw/workspace/sentinel.log`

---

## Cron

Cron is considered:

- **OK** when:
  - `openclaw cron list` shows all core jobs (usage-monitor, model-health, daily-backup, weekly-log-cleanup, weekly-curiosity, moltx-poster) with `Status: ok` or `idle`.

- **WARN/FAIL** when:
  - any of the above shows `Status: error` or `missing`.

Immediate actions:

1. Inspect: `openclaw cron inspect <id>`
2. Restart specific jobs or the gateway if needed.

---

## Ops State File

`ops_inbox.py` writes a structured snapshot:

```json
{
  "timestamp": "2026-03-02T23:59:00Z",
  "gateway": "ok" | "warn",
  "sentinel": "ok" | "warn",
  "cron": "ok"
}
```

Other tools (or future UIs) can read `ops_state.json` instead of parsing logs.
