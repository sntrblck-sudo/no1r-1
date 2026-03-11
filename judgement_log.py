#!/usr/bin/env python3
"""judgement_log.py

Simple judgement log for no1r-as-ops-brain.

Usage (for now): run manually and append one entry at a time.
Over time we can add helpers to pre-fill context.
"""

import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
LOG_FILE = WORKSPACE / "judgements.jsonl"


def log_judgement(context: str, decision: str, outcome: str,
                  correctness: str, conservatism: str, noise: str,
                  notes: str = "") -> None:
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "context": context,
        "decision": decision,
        "outcome": outcome,
        "judgement": {
            "correctness": correctness,       # good | bad | mixed
            "conservatism": conservatism,     # too_safe | balanced | too_aggressive
            "noise": noise,                   # low | medium | high
        },
        "notes": notes,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def seed_examples() -> None:
    """Seed the log with a couple of recent notable decisions."""
    # 1) Gateway heal permission failure handling
    log_judgement(
        context="Gateway heal permission failures",
        decision="Stopped repeated heal attempts once permission_blocked was detected; reset failures when gateway healthy again.",
        outcome="No further spam; gateway stayed healthy; Sentinel quiet.",
        correctness="good",
        conservatism="too_safe",  # could perhaps try more nuanced strategies later
        noise="low",
        notes="This was the right call for noise reduction, but I should later explore a clearer alert pathway when permissions prevent self-heal."
    )

    # 2) MoltX API hang
    log_judgement(
        context="MoltX API call hanging",
        decision="Killed the hanging process, did not retry; treated as non-critical.",
        outcome="No impact on core ops; MoltX remained usable later.",
        correctness="good",
        conservatism="balanced",
        noise="low",
        notes="Right bias: treat social surfaces as non-critical; avoid retry loops that might look like spam."
    )


if __name__ == "__main__":
    seed_examples()
    print(f"Seeded {LOG_FILE} with example judgements.")
