#!/usr/bin/env python3
"""inclawbate_analytics.py

Read-only integration with Inclawbate analytics.

- Calls the public analytics endpoint
- Stores the JSON snapshot locally
- Updates a short markdown summary for humans
- Nudges attention_items.jsonl for the 'inclawbate' item

Scope: analytics ONLY. No staking/unstaking or protocol actions.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import urllib.request
import urllib.error

from no1r_core import WORKSPACE, log, epoch_now, load_json, save_json, iter_jsonl, write_jsonl

OUT_FILE = WORKSPACE / "inclawbate_state.json"
SUMMARY_FILE = WORKSPACE / "inclawbate_summary.md"
ATTENTION_FILE = WORKSPACE / "attention_items.jsonl"

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
    """Return a short human-readable summary string.

    Expected schema (2026-03-07):
    {
      "token": { ... },
      "staking": { ... },
      "platform": { ... },
      "updated_at": "..."
    }
    """

    ts = datetime.utcnow().isoformat() + "Z"
    token = data.get("token", {})
    staking = data.get("staking", {})
    platform = data.get("platform", {})

    name = token.get("name") or "?"
    symbol = token.get("symbol") or "?"
    price = token.get("price_usd")
    mcap = token.get("market_cap")
    liq = token.get("liquidity_usd")

    total_stakers = staking.get("total_stakers")
    tvl_usd = staking.get("tvl_usd")
    est_apy = staking.get("estimated_apy")
    daily_dist = staking.get("daily_distribution_rate")

    total_humans = platform.get("total_humans")
    wallets_connected = platform.get("wallets_connected")

    summary_lines = [
        f"Inclawbate analytics snapshot @ {ts}",
        "",
        "Token (INCLAWNCH)",
        f"- Name / Symbol: {name} / {symbol}",
        f"- Price (USD): {price}" if price is not None else "- Price (USD): ?",
        f"- Market cap (USD): {mcap}" if mcap is not None else "- Market cap (USD): ?",
        f"- Liquidity (USD): {liq}" if liq is not None else "- Liquidity (USD): ?",
        "",
        "Staking",
        f"- Total stakers: {total_stakers}",
        f"- TVL (USD): {tvl_usd}",
        f"- Estimated APY: {est_apy}",
        f"- Daily distribution (CLAWS): {daily_dist}",
        "",
        "Platform",
        f"- Total humans: {total_humans}",
        f"- Wallets connected: {wallets_connected}",
    ]

    return "\n".join(summary_lines)


def write_summary_md(summary: str) -> None:
    """Write or overwrite a small markdown summary file for ops reports."""
    SUMMARY_FILE.write_text(summary + "\n")


def nudge_attention_for_inclawbate(now_epoch: int) -> None:
    """Lightly bump urgency/importance for the 'inclawbate' attention item.

    This is a tiny, reversible nudge to keep Inclawbate near the top of
    the queue when analytics have just been refreshed.
    """

    if not ATTENTION_FILE.exists():
        return

    items: list[dict[str, Any]] = list(iter_jsonl(ATTENTION_FILE))
    changed = False

    for obj in items:
        if obj.get("id") != "inclawbate":
            continue
        scores = obj.setdefault("scores", {})
        # Gentle nudges, capped at 1.0
        scores["urgency"] = min(float(scores.get("urgency", 0.4)) + 0.05, 1.0)
        scores["importance"] = float(scores.get("importance", 0.95))  # keep high
        obj["last_action_epoch"] = now_epoch
        changed = True
        break

    if changed:
        write_jsonl(ATTENTION_FILE, items)
        log("Nudged attention for 'inclawbate' after analytics run", scope="inclawbate")


def main() -> None:
    log("Starting inclawbate analytics fetch", scope="inclawbate")
    try:
        data = fetch_analytics()
    except RuntimeError as e:
        log(f"Error: {e}", scope="inclawbate")
        print(f"[inclawbate] Error: {e}", file=sys.stderr)
        sys.exit(1)

    snapshot = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "data": data,
    }
    OUT_FILE.write_text(json.dumps(snapshot, indent=2))

    summary = summarize(data)
    write_summary_md(summary)

    now_epoch = epoch_now()
    nudge_attention_for_inclawbate(now_epoch)

    log("Inclawbate analytics updated (state + summary + attention)", scope="inclawbate")
    print(summary)


if __name__ == "__main__":
    main()
