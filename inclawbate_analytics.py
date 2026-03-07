#!/usr/bin/env python3
"""inclawbate_analytics.py

Read-only integration with Inclawbate analytics.

- Calls the public analytics endpoint
- Stores the JSON snapshot locally
- Updates a short markdown summary for humans

Scope: analytics ONLY. No staking/unstaking or protocol actions.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import urllib.request
import urllib.error

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
OUT_FILE = WORKSPACE / "inclawbate_state.json"
SUMMARY_FILE = WORKSPACE / "inclawbate_summary.md"

API_URL = "https://www.inclawbate.com/api/inclawbate/analytics"


def fetch_analytics() -> dict:
    req = urllib.request.Request(API_URL, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Inclawbate analytics HTTP error: {e.code} {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Inclawbate analytics connection error: {e}") from e

    try:
        data = json.loads(body)
    except Exception as e:
        raise RuntimeError(f"Unexpected Inclawbate response: {body[:200]}...") from e

    return data


def summarize(data: dict) -> str:
    """Return a short human-readable summary string."""
    ts = datetime.utcnow().isoformat() + "Z"
    summary_lines = [f"Inclawbate analytics snapshot @ {ts}"]

    # Common-style fields we might expect (adjust as we learn real schema)
    total_staked = data.get("totalStaked") or data.get("tvl")
    ubi_distributed = data.get("ubiDistributed") or data.get("totalUBI")
    participants = data.get("participants") or data.get("stakers")

    if total_staked is not None:
        summary_lines.append(f"- Total staked: {total_staked}")
    if ubi_distributed is not None:
        summary_lines.append(f"- UBI distributed: {ubi_distributed}")
    if participants is not None:
        summary_lines.append(f"- Participants: {participants}")

    if len(summary_lines) == 1:
        summary_lines.append("- (Schema unknown; raw JSON stored in inclawbate_state.json)")

    return "\n".join(summary_lines)


def write_summary_md(summary: str) -> None:
    """Write or overwrite a small markdown summary file for ops reports."""
    SUMMARY_FILE.write_text(summary + "\n")


def main() -> None:
    try:
        data = fetch_analytics()
    except RuntimeError as e:
        print(f"[inclawbate] Error: {e}", file=sys.stderr)
        sys.exit(1)

    snapshot = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "data": data,
    }
    OUT_FILE.write_text(json.dumps(snapshot, indent=2))

    summary = summarize(data)
    write_summary_md(summary)

    print(summary)


if __name__ == "__main__":
    main()
