#!/usr/bin/env python3
"""ops_daily_report.py

Generate a quick "last 24h" ops report:
- Current ops_state
- Sentinel key log lines from last 24h
- Recent judgements (if any)
- Recent git commits (ops-relevant)

Read-only, writes to ops_daily_report.md for convenience.
"""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
OPS_STATE_FILE = WORKSPACE / "ops_state.json"
JUDGEMENTS_FILE = WORKSPACE / "judgements.jsonl"
REPORT_FILE = WORKSPACE / "ops_daily_report.md"


def run(cmd: str) -> str:
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return proc.stdout.strip() or proc.stderr.strip()


def load_ops_state() -> dict:
    try:
        return json.loads(OPS_STATE_FILE.read_text())
    except Exception:
        return {}


def load_recent_judgements(hours: int = 24) -> list:
    if not JUDGEMENTS_FILE.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    entries = []
    with open(JUDGEMENTS_FILE) as f:
        for line in f:
            try:
                d = json.loads(line)
                ts = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
                if ts >= cutoff:
                    entries.append(d)
            except Exception:
                continue
    return entries


def load_recent_commits(hours: int = 24) -> str:
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    cmd = f"cd {WORKSPACE} && git log --since=\"{cutoff}\" --oneline | head"
    return run(cmd)


def load_sentinel_log(hours: int = 24) -> str:
    # Simple approach: show last 40 lines; Sentinel log is already time-filtered enough for now.
    # Could be enhanced to filter by timestamp if needed.
    return run(f"tail -40 {WORKSPACE/'sentinel.log'} 2>&1")


def main() -> None:
    now = datetime.utcnow().isoformat() + "Z"
    state = load_ops_state()
    judgements = load_recent_judgements()
    commits = load_recent_commits()
    sentinel_tail = load_sentinel_log()

    lines = []
    lines.append(f"# Ops Daily Report\n")
    lines.append(f"Generated: {now}\n")

    lines.append("## Ops State\n")
    if state:
        lines.append("```json")
        lines.append(json.dumps(state, indent=2))
        lines.append("```")
    else:
        lines.append("(no ops_state.json found)")

    lines.append("\n## Sentinel (tail -40)\n")
    lines.append("```text")
    lines.append(sentinel_tail)
    lines.append("```")

    lines.append("\n## Recent Judgements (24h)\n")
    if judgements:
        for j in judgements:
            lines.append(f"- {j['timestamp']} — {j['context']} — correctness={j['judgement']['correctness']}, conservatism={j['judgement']['conservatism']}, noise={j['judgement']['noise']}")
    else:
        lines.append("- (none in last 24h)")

    lines.append("\n## Recent Commits (24h)\n")
    if commits:
        lines.append("```text")
        lines.append(commits)
        lines.append("```")
    else:
        lines.append("(no commits in last 24h)")

    REPORT_FILE.write_text("\n".join(lines))
    print(f"Written {REPORT_FILE}")


if __name__ == "__main__":
    main()
