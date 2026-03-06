# Panic Playbook - no1rlocal

If something feels wrong (no replies, errors, weird alerts), walk this in order.

---

## 1. Check Gateway

From the host:

```bash
openclaw status
```

Look at:
- **Gateway** line – should be `reachable` with low ms latency
- **Gateway service** – should be `running`

If it’s **stopped**:

```bash
openclaw gateway start
# or, if needed
sudo systemctl restart openclaw-gateway
```

If it keeps failing, stop here and ask for help.

---

## 2. Check Sentinel

```bash
sudo systemctl status sentinel
```

Healthy:
- `Active: active (running)`

If it’s failed:

```bash
sudo systemctl restart sentinel
```

Quick sanity:

```bash
tail -40 ~/\.openclaw/workspace/sentinel.log
curl -s http://localhost:18799/health
```

You should see:
- `"status": "ok"`
- Reasonable `failures` and `restarts` counts (often 0)

---

## 3. Check Autocommit + Git

```bash
sudo systemctl status autocommit
cd ~/\.openclaw/workspace
git status -sb
```

Healthy:
- Autocommit `active (running)`
- `git status` shows only small, expected changes

If autocommit is down:

```bash
sudo systemctl restart autocommit
```

If git remote feels stale:

```bash
cd ~/\.openclaw/workspace
git pull --rebase origin main   # only if you know nothing critical changed locally
```

---

## 4. Check Cron Jobs (When Jobs Look Suspicious)

If a cron job seems off (missed runs, no output, or silent failures), walk this ladder:

```bash
openclaw cron status                      # Is the cron scheduler enabled?
openclaw cron list                        # Is the job enabled with a valid schedule?
openclaw cron runs --id <jobId> --limit 20  # Recent runs + error messages
openclaw logs                             # Gateway-level errors
openclaw channels status --probe          # Delivery channels healthy?
```

If the job delivers to channels, prefer `delivery.bestEffort: true` to avoid hard failures when targets are temporarily unreachable.

For critical jobs, consider:
- Explicit `--tz` (e.g. `America/New_York`)
- Reasonable intervals (avoid <5 minutes; use seconds-based cron only for very simple sub-minute tasks)
- `--session isolated` for non-trivial work

---

## 5. Restore Test (Dry Run Only)

To **verify** backups (no live overwrite):

```bash
LATEST=$(ls -t ~/openclaw-backups/openclaw-*.tar.gz | head -1)
mkdir -p /tmp/openclaw-restore-test
rm -rf /tmp/openclaw-restore-test/*
tar -xzf "$LATEST" -C /tmp/openclaw-restore-test
ls -la /tmp/openclaw-restore-test/.openclaw/workspace | head
```

You should see a full workspace with:
- `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `MEMORY.md`
- `sentinel.py`, `autocommit.py`, `skills/`, `config/`, `memory/`, etc.

**Do NOT** copy this over `~/.openclaw` without a deliberate restore plan.

---

## 5. Telegram Alerts

If Telegram is noisy or stale:

- Alerts are controlled by `telegram_alerts.py` + `.pending_alerts.json`
- Hourly Sentinel status is **disabled by default**.

To hard-reset alerts:

```bash
cd ~/\.openclaw/workspace
rm -f .pending_alerts.json
# Then restart the alerts runner if one is active
# (usually managed by a separate process, not systemd here)
```

---

## 6. When to Call It

Stop and ask for help if:

- `openclaw status` shows Gateway unreachable after a manual restart
- Sentinel log is **spamming errors** after a restart
- `curl http://localhost:18799/health` returns anything other than a small JSON object with `status` and numbers
- Backups fail to extract cleanly under `/tmp/openclaw-restore-test`

Document what you ran and the last 40 lines of:

```bash
tail -40 ~/\.openclaw/workspace/sentinel.log
openclaw status
```

and paste that into the conversation.
