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

from no1r_core import WORKSPACE, log


def _run_script(name: str) -> int:
    """Run a workspace-local Python script and return its exit code."""
    script = WORKSPACE / name
    if not script.exists():
        log(f"Script not found: {name}", scope="registry")
        return 1
    proc = subprocess.run(["python3", name], cwd=WORKSPACE, check=False)
    if proc.returncode != 0:
        log(f"Script {name} exited with {proc.returncode}", scope="registry")
    return proc.returncode


def run_inclawbate_analytics() -> None:
    """Run inclawbate analytics and then refresh attention tension."""
    log("Running inclawbate_analytics.py", scope="inclawbate")
    rc = _run_script("inclawbate_analytics.py")
    if rc != 0:
        log("Skipping attention_tension due to inclawbate analytics failure", scope="registry")
        return
    # On success, refresh attention priorities
    log("Running attention_tension.py after inclawbate analytics", scope="attention")
    _run_script("attention_tension.py")


def run_attention_tension() -> None:
    log("Running attention_tension.py", scope="attention")
    _run_script("attention_tension.py")


def run_ops_inbox() -> None:
    log("Running ops_inbox.py", scope="ops")
    _run_script("ops_inbox.py")


def run_patterns_mirror() -> None:
    log("Running patterns_mirror.py", scope="patterns")
    _run_script("patterns_mirror.py")


def run_finance_simulation() -> None:
    log("Running finance_simulation.py (simulation only)", scope="finance")
    _run_script("finance_simulation.py")


ACTIONS = {
    "inclawbate-analytics": run_inclawbate_analytics,
    "attention-tension": run_attention_tension,
    "ops-inbox": run_ops_inbox,
    "patterns-mirror": run_patterns_mirror,
    "finance-sim": run_finance_simulation,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="no1r action registry")
    parser.add_argument("--task", choices=sorted(ACTIONS.keys()), required=True)
    args = parser.parse_args()

    action = ACTIONS[args.task]
    action()


if __name__ == "__main__":
    main()
