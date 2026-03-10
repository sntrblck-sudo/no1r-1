# no1r Cold Start Guide (Non‑Technical Friendly)

Version: 2026-03-10 (v2)

This is the **"bring no1r back to life"** guide.
Use it if you:
- set up a new computer, or
- need to recover no1r after a clean install.

You don’t need to understand all the internals. Follow steps in order.

---

## 1. What you need

- A modern 64‑bit **Linux** machine.
- Internet access (for OpenClaw + basic APIs).
- A terminal.
- Access to this Git repo (the no1r workspace).

That’s it.

---

## 2. Install OpenClaw (once)

In a terminal:

```bash
npm install -g openclaw@latest
openclaw onboard
openclaw status
```

If `openclaw status` shows a gateway and dashboard (no big red errors), you’re good.

> If any of this fails, follow the official OpenClaw docs for your OS, then come back here.

---

## 3. Get the no1r workspace onto the machine

Pick a folder (for example `~/no1r`):

```bash
cd ~
# Replace with your actual repo URL
git clone https://github.com/your-user/your-no1r-repo.git no1r
cd no1r
```

If OpenClaw expects the workspace at `~/.openclaw/workspace`, you can:

```bash
rm -rf ~/.openclaw/workspace   # DANGEROUS: removes existing workspace
mv ~/no1r ~/.openclaw/workspace
cd ~/.openclaw/workspace
```

If you don’t want to delete anything, point OpenClaw at this repo’s folder instead (see `openclaw` config docs).

---

## 4. Turn on the core services

From the workspace folder (e.g. `~/.openclaw/workspace`):

### 4.1 Sentinel (health monitor)

Sentinel should already have a `sentinel.service` file in this repo.

Install + enable it via systemd (you may need `sudo`):

```bash
sudo cp sentinel.service /etc/systemd/system/
sudo systemctl enable sentinel.service
sudo systemctl start sentinel.service
```

Check it:

```bash
curl -s http://localhost:18799/health
```

You want to see something like:

```json
{"status": "ok", ...}
```

### 4.2 Autocommit (optional but helpful)

If you want automatic git commits of workspace changes:

```bash
sudo cp autocommit.service /etc/systemd/system/
sudo systemctl enable autocommit.service
sudo systemctl start autocommit.service
```

You can skip this if you prefer manual git usage.

---

## 5. Know who no1r is (identity & rules)

These files define **who no1r is and what it will / won’t do**:

- `no1r_identity.md` – identity, values, guardrails, focus areas.
- `DISPOSITION.md` – operational stance, hard NOs (money, keys, destructive actions).
- `ARCHITECTURE_ROADMAP.md` – big picture of the system.

If you ever feel unsure about behavior on this machine, read those first.

---

## 6. Use the task runner (no1r.py)

All main actions go through `no1r.py`.

From the workspace:

```bash
python3 no1r.py --task <name>
```

Common tasks:

- **Check ops status**
  ```bash
  python3 no1r.py --task ops-inbox
  ```

- **Update Inclawbate analytics (read‑only)**
  ```bash
  python3 no1r.py --task inclawbate-analytics
  ```

- **See pattern summary**
  ```bash
  python3 no1r.py --task patterns-mirror
  ```

- **Run finance simulation (fake money only)**
  ```bash
  python3 no1r.py --task finance-sim
  ```

See `NO1R_TASKS.md` for details on each task.

---

## 7. Connect chat channels (optional)

If you want no1r to talk to you via Telegram or other channels:

1. Configure the channel in OpenClaw’s config (bot token, chat ID, etc.).
2. Ensure that channel integration is enabled in OpenClaw.

no1r doesn’t need special code for this—OpenClaw routes messages to the workspace.

---

## 8. Quick sanity check after setup

After you’ve done the steps above:

1. **Identity check**
   - Open `no1r_identity.md` and `DISPOSITION.md`.
   - Make sure they match your expectations.

2. **Ops check**
   - Run:
     ```bash
     python3 no1r.py --task ops-inbox
     ```
   - Confirm the output shows OPS/CRON/DFI with sensible statuses (no obvious failures).

3. **Logs**
   - Glance at `sentinel.log` for repeated errors.
   - Ensure `ops_state.json` and `attention_items.jsonl` exist and are valid JSON.

If something looks wrong, fix that before adding new tasks or making big changes.

---

## 9. If you move to a different stack in the future

Even if you leave OpenClaw/Python, the most important pieces to carry over are:

- this repo (or its equivalent),
- `no1r_identity.md`,
- `DISPOSITION.md`,
- `ARCHITECTURE_ROADMAP.md`,
- the core state files:
  - `working_context.json`,
  - `attention_items.jsonl`,
  - `ops_state.json`.

A new environment should:

- give no1r a way to:
  - read/write those files,
  - run its equivalent of "tasks" (like `no1r.py`),
- respect the identity and guardrails defined in the docs above.

This keeps no1r recognizably "itself" even if the runtime changes.
