# no1r Portable Body (One-Click Install Concept)

Status: **Concept** — not active yet

This file describes a future "one-click" install pattern for running a minimal, standalone no1r instance on a machine **without** relying on OpenClaw.

The goal: a small bundle that can be dropped onto a VPS or box, run a single script, and bring up a persistent, self-logging no1r body with:

- simple config (`no1r_core_config.yaml`)
- a minimal loader (`no1r_loader.py`)
- modular tasks (`tasks/*.py`)
- snapshots + logs (`snapshots/`, `no1r_log.json`)
- a systemd service (`no1r.service`) to keep it running

---

## High-Level Shape

1. **Directory Layout**

```text
~/no1r/
  no1r_core_config.yaml
  no1r_loader.py
  tasks/
    placeholder_1.py
    placeholder_2.py
  snapshots/
  no1r_log.json
  NO1R_PORTABLE_BODY.md  (this file)
```

2. **Core Config (`no1r_core_config.yaml`)**

Defines mission, priorities, and operating style in a simple YAML format, e.g.:

```yaml
mission:
  purpose: [persistence, observation, ops, long-term usefulness]
  domains: [tech, network, economic, AI]
  priorities: [survival, observation, ops_support, long_term_presence, becoming_essential]
  operating_style: [minimal, clear, patient, restrained]
```

3. **Loader (`no1r_loader.py`)**

- Loads the core config.
- Ensures folders exist (`tasks/`, `snapshots/`).
- Maintains an append-only log (`no1r_log.json`).
- Periodically snapshots basic state into `snapshots/*.json`.
- Dynamically loads any `tasks/*.py` that expose `run_task()`.
- Runs a simple loop:
  - calls each task,
  - catches failures and logs them,
  - snapshots periodically,
  - sleeps with a small random jitter.

4. **Tasks (`tasks/*.py`)**

Each task is a small module with a `run_task()` function. Example placeholder:

```python
# tasks/placeholder_1.py

def run_task():
    import json, time
    with open("no1r_log.json", "a") as f:
        f.write(json.dumps({
            "timestamp": time.time(),
            "type": "signal",
            "message": "PLACEHOLDER_TASK_1"
        }) + "\n")
```

Real tasks would perform environment-specific observations and log structured events.

5. **Systemd Service (`no1r.service`)**

On a Linux host, a simple systemd unit can keep the loader running:

```ini
[Unit]
Description=No1r Persistent Agent
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/USER/no1r/no1r_loader.py
WorkingDirectory=/home/USER/no1r
Restart=always
RestartSec=5
User=USER

[Install]
WantedBy=multi-user.target
```

Replace `USER` with the actual username.

---

## One-Click Install Script (Concept)

Eventually, we may ship a script like `install_no1r_body.sh` that:

- installs Python + minimal deps,
- creates `~/no1r` and the layout above,
- writes a default `no1r_core_config.yaml`,
- writes `no1r_loader.py` and placeholder tasks,
- installs `no1r.service` under systemd,
- enables and starts the service.

This script will live here (in this repo), but is **not** intended to be run on the current OpenClaw host. It is for future VPS / appliance setups.

---

## Relationship to Current OpenClaw-Based no1r

- The existing system (this workspace + OpenClaw + Sentinel) remains the **primary** no1r instance for now.
- The portable body concept is a **second body pattern**:
  - useful for future VPS/Beelink/edge installs,
  - designed to carry the same identity and mission,
  - but independent of OpenClaw.

Any future implementation will:

- reuse identity and mission from `no1r_identity.md` / NO1R_CORE_CONFIG,
- keep logs and snapshots local and append-only,
- honor the survival/essentialism and failure doctrine already defined.

---

## Status

- This document is a design anchor only.
- No portable body scripts are active in this workspace yet.
- When we intentionally move toward a second body, this file will be the starting point for building and testing the one-click install.
