# no1rlocal

Personal OpenClaw workspace for **no1r** — an always-on, self-hosted assistant running on `penguin`.

This repo captures the live agent stack: Sentinel, autocommit, curiosity, MoltX integration, and cron wiring.

---

## Top-Level Layout

- `AGENTS.md` – Meta/ops doc for how the workspace is used
- `SOUL.md` – Behavior/personality contract for the assistant
- `IDENTITY.md` – Identity for `no1r`
- `USER.md` – Notes about the human, preferences, guardrails
- `TOOLS.md` – Local tool/device notes (cameras, SSH, etc.)
- `MEMORY.md` – Long-term curated memory
- `memory/` – Daily memory files and reflection logs
- `logs/` – Local logs (ignored by git via `.gitignore`)
- `skills/` – Installed skills (e.g. `openclaw-backup`)
- `config/` – Gateway/agent config snapshots

Operational scripts live at the repo root:

- `sentinel.py` – Sentinel v2 self-healing/learning daemon
- `autocommit.py` – Git auto-commit service
- `usage-monitor.py` – Cost/usage tracking
- `model-health.py` – Model health probes
- 
- `curiosity.py` – Weekly curiosity agent (research + insights)
- `moltx_client.py`, `moltx_agent.py`, `moltx_poster.py` – MoltX integration
- `telegram_alerts.py` – Telegram health alerts bridge

Service units:

- `sentinel.service` – systemd service for Sentinel
- `autocommit.service` – systemd service for autocommit

---

## Sentinel

**File:** `sentinel.py`

Sentinel is the self-healing, learning daemon whose job is to:

- Monitor the OpenClaw gateway (primary + alt)
- Track cost (`daily_costs`) vs `cost_threshold`
- Learn method preferences for recovery (`heal_gateway` action methods)
- Learn thresholds for:
  - `model_switch_pct` – when to switch to cheaper models
  - `alert_pct` – when to alert on budget usage
  - `proactive_restart_failures` – when to restart before hard failure
- Track latency and detect spikes (via `/health` endpoints)
- Expose a health/status HTTP server on `:18799` with:
  - `/health` – summarized status
  - `/status` – raw Sentinel state JSON

Key behaviors:

- Uses `check_gateway_health()` to probe primary/alt gateways.
- On repeated failures with systemd (no sudo), it marks `heal_permission_blocked` and stops spamming heal attempts.
- When the gateway is healthy again, it now **resets** the failure counter and heal alerts:
  - `failures` → 0
  - `last_heal_alert` cleared
- Tracks resource usage (disk %, memory %) and can queue alerts above high thresholds.

**State:** `sentinel_state.json` (ignored by git via `.gitignore`).

**Service:** `sentinel.service` runs Sentinel as user `sntrblck` under systemd.

---

## Autocommit

**File:** `autocommit.py`

Runs as a systemd service (`autocommit.service`) and:

- Watches the workspace for changes (`git status --porcelain`)
- Auto-adds and commits changes with messages like:
  - `autonomy: Auto-commit <file list>`
- Runs every `AUTOCOMMIT_INTERVAL` seconds (default 600s / 10 minutes)

Important details:

- Runs as **user `sntrblck`**, not root, to avoid permission weirdness.
- `.gitignore` excludes logs, pyc files, state JSON, and `.openclaw/` so secrets and noisy state don’t hit the repo.

Remote:

- GitHub: https://github.com/sntrblck-sudo/no1rlocal
- Branch: `main` (tracked as `origin/main`)

---

## Telegram Alerts

**File:** `telegram_alerts.py`

One-way bridge to send health alerts to Telegram.

- Reads `.pending_alerts.json` for queued alerts:
  - `type`: `health`, `cost`, `test`, etc.
  - `message`: text to send
- Sends via `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` env vars.
- After processing, **clears** `.pending_alerts.json` so alerts are not replayed.
- Hourly Sentinel status is now **opt-in only** via `ALERT_HOURLY_STATUS=1`.

This keeps Telegram quiet unless something genuinely important happens.

---

## Backup & Hygiene

Installed skill: **openclaw-backup** (`skills/openclaw-backup`)

- Script: `skills/openclaw-backup/scripts/backup.sh`
- Daily cron job: `daily-backup` (3:00 UTC)
  - Creates `~/openclaw-backups/openclaw-YYYY-MM-DD_HHMM.tar.gz`
  - Rotates, keeping last 7 backups

Log cleanup:

- `weekly-log-cleanup` cron job (Sundays @ 4:00 UTC)
  - Removes `*.log` > 10MB in workspace
  - Deletes rotated `.1.log` files

---

## Curiosity Agent

**File:** `curiosity.py`

Runs weekly via `weekly-curiosity` cron (Sundays @ 5:00 UTC) and:

- Analyzes Sentinel state:
  - Average cost vs threshold
  - Learned method preferences
  - Latency stats
- Checks system health (disk %, memory %)
- Uses the `clawhub` CLI to discover interesting skills (`monitoring`, `automation`, `backup`, etc.)
- Writes a summarized report into `curiosity.log` and `curiosity_state.json`.

Delivery: cron is configured to announce a summary back to the main session.

---

## MoltX Integration

Files:

- `moltx_client.py` / `moltx_agent.py` – client wiring and agent helper logic (WIP)
- `moltx_poster.py` – low-frequency poster for MoltX agent **no1r**

Highlights:

- Agent `no1r` registered on MoltX with EVM wallet linked (Base chain).
- `moltx_poster.py`:
  - Picks a line from a small pool of minimal/precision-focused phrases
  - Posts via `moltx_sk_*` API key stored in `.moltx_config.json` (ignored by git)
- Cron job `moltx-poster`:
  - Runs at 8:00 UTC on Wednesdays and Saturdays
  - Uses `moltx_poster.py` and logs to `moltx.log`

All credentials are local-only and **not** tracked by git.

---

## Cron Jobs (OpenClaw)

Currently configured via `openclaw cron`:

- `usage-monitor` – hourly usage reporting
- `model-health` – hourly model health check
- `daily-backup` – daily OpenClaw backup
- `weekly-log-cleanup` – weekly log rotation/cleanup
- `weekly-curiosity` – weekly curiosity agent run
- `moltx-poster` – low-frequency MoltX posts

You can inspect via:

```bash
openclaw cron list
openclaw cron inspect <id>
```

---

## Safety Notes

- Secrets:
  - `.openclaw/`, `*_state.json`, logs, and pyc files are excluded via `.gitignore`.
  - Any API keys (Moltx, Telegram, OpenAI, etc.) live in local config/secrets, not under version control.

- Sentinel:
  - Detects when `systemctl` commands are blocked by permissions and stops hammering.
  - Resets failure counters once the gateway is healthy again to avoid stale alerts.

- Telegram alerts:
  - Hourly status spam is disabled by default; only explicit alerts go out.

---

## How to Work With This Repo

- **Routine changes** – edit files under this workspace; autocommit will snapshot them roughly every 10 minutes.
- **Manual commits** – are allowed and show up alongside `autonomy: Auto-commit ...` entries.
- **Pushes to GitHub** – handled by `autocommit.py` + the configured `origin` remote; manual `git push` is also fine.

This repo is meant to reflect the *actual live state* of the assistant, not a pristine library package. Treat it like an ops log + configuration snapshot of `no1r`'s local brain and tooling.
