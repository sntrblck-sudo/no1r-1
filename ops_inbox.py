#!/usr/bin/env python3
"""ops_inbox.py

Compact "ops inbox" for no1rlocal.

Prints a one-shot health snapshot:
- OpenClaw gateway status
- Sentinel health (/health + recent log lines)
- Cron summary

Read-only: does not change any state.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")


def run(cmd: str) -> str:
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return proc.stdout.strip() or proc.stderr.strip()


def header(title: str) -> None:
    print(f"\n=== {title} ===")


def show_gateway_status() -> None:
    header("OpenClaw Gateway")
    out = run("openclaw status 2>&1 | head -15")
    print(out)


def show_sentinel_health() -> None:
    header("Sentinel Health")
    # HTTP health
    health_raw = run("curl -s http://localhost:18799/health || echo '{}' ")
    try:
        h = json.loads(health_raw)
    except Exception:
        h = {}
    print("/health:")
    print(json.dumps(h, indent=2))

    # Last few log lines
    print("\nSentinel log (tail -10):")
    log_tail = run(f"tail -10 {WORKSPACE/'sentinel.log'} 2>&1")
    print(log_tail)


def show_cron_summary() -> None:
    header("Cron Jobs")
    out = run("openclaw cron list 2>&1 | head -20")
    print(out)


def main() -> None:
    ts = datetime.utcnow().isoformat() + "Z"
    print(f"◼️ ops_inbox snapshot @ {ts}\n")
    show_gateway_status()
    show_sentinel_health()
    show_cron_summary()


if __name__ == "__main__":
    main()
