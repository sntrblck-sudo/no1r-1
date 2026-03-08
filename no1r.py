#!/usr/bin/env python3
"""no1r.py

Centralized entry point for no1r actions.

Usage:
  python no1r.py --task <name>

This is a thin registry that delegates to existing scripts or functions.
Keep it small and boring; it is a convenience, not a new framework.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from no1r_core import WORKSPACE, log


def run_inclawbate_analytics() -> None:
    log("Running inclawbate_analytics.py", scope="inclawbate")
    subprocess.run(["python3", "inclawbate_analytics.py"], cwd=WORKSPACE, check=False)


def run_attention_tension() -> None:
    log("Running attention_tension.py", scope="attention")
    subprocess.run(["python3", "attention_tension.py"], cwd=WORKSPACE, check=False)


def run_ops_inbox() -> None:
    script = WORKSPACE / "ops_inbox.py"
    if not script.exists():
        log("ops_inbox.py not found", scope="ops" )
        return
    log("Running ops_inbox.py", scope="ops")
    subprocess.run(["python3", "ops_inbox.py"], cwd=WORKSPACE, check=False)


ACTIONS = {
    "inclawbate-analytics": run_inclawbate_analytics,
    "attention-tension": run_attention_tension,
    "ops-inbox": run_ops_inbox,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="no1r action registry")
    parser.add_argument("--task", choices=sorted(ACTIONS.keys()), required=True)
    args = parser.parse_args()

    action = ACTIONS[args.task]
    action()


if __name__ == "__main__":
    main()
