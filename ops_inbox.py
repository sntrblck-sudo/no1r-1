#!/usr/bin/env python3
"""ops_inbox.py

Tension-aware "ops inbox" for no1rlocal.

Prints a compact, prioritized health snapshot:
- Top 3 domains by tension (e.g., Sentinel/Gateway, Inclawbate, Cron)
- Brief raw details for quick inspection

Read-only: does not change any external state beyond writing ops_state.json.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from no1r_core import WORKSPACE, log, iter_jsonl

import subprocess


def run(cmd: str) -> str:
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return proc.stdout.strip() or proc.stderr.strip()


OPS_STATE_FILE = WORKSPACE / "ops_state.json"
ATTENTION_FILE = WORKSPACE / "attention_items.jsonl"


def write_state(state: dict[str, Any]) -> None:
    try:
        OPS_STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


# ---------- health probes ----------


def probe_gateway() -> dict[str, Any]:
    raw = run("openclaw status 2>&1 | head -15")
    status = "ok" if "Gateway         │ local" in raw and "reachable" in raw else "warn"
    return {"domain": "gateway", "status": status, "raw": raw}


def probe_sentinel() -> dict[str, Any]:
    health_raw = run("curl -s http://localhost:18799/health || echo '{}' ")
    try:
        h = json.loads(health_raw)
    except Exception:
        h = {}
    status = "ok" if h.get("status") == "ok" else "warn"

    log_tail = run(f"tail -10 {WORKSPACE/'sentinel.log'} 2>&1")
    return {"domain": "sentinel", "status": status, "health": h, "log_tail": log_tail}


def probe_cron() -> dict[str, Any]:
    raw = run("openclaw cron list 2>&1 | head -20")
    # Very simple heuristic: if command runs, treat as ok for now
    status = "ok" if raw else "warn"
    return {"domain": "cron", "status": status, "raw": raw}


# ---------- tension-aware ranking ----------


def load_attention_map() -> dict[str, dict[str, Any]]:
    """Return a mapping from attention id to its JSON object."""
    mapping: dict[str, dict[str, Any]] = {}
    if not ATTENTION_FILE.exists():
        return mapping
    for obj in iter_jsonl(ATTENTION_FILE):
        _id = str(obj.get("id"))
        mapping[_id] = obj
    return mapping


def domain_tension(domain: str, attention: dict[str, dict[str, Any]]) -> float:
    """Return a simple tension score for a domain.

    Currently:
    - gateway + sentinel → use attention["inclawbate"]? No, we keep them separate.
    - sentinel/gateway → base on any "ops"-like items if present, else 0.7.
    - inclawbate → use attention["inclawbate"] scores if present.
    - cron → base on any "automation"-like item if present, else 0.5.

    For now we keep it simple and mostly static, using attention where available.
    """

    # Defaults if we lack explicit attention items
    defaults = {
        "gateway": 0.8,
        "sentinel": 0.8,
        "cron": 0.6,
        "inclawbate": 0.75,
    }

    if domain == "inclawbate":
        item = attention.get("inclawbate")
        if item:
            scores = item.get("scores", {})
            return float(scores.get("importance", 0.8))

    # For now, use defaults; future: map specific attention IDs to domains
    return defaults.get(domain, 0.5)


def main() -> None:
    ts = datetime.utcnow().isoformat() + "Z"
    print(f"◼️ ops_inbox snapshot @ {ts}\n")

    # Probes
    gateway = probe_gateway()
    sentinel = probe_sentinel()
    cron = probe_cron()

    # Placeholder Inclawbate domain (uses analytics state, not live fetch)
    incl_state: dict[str, Any] = {}
    incl_status = "observe"
    incl_path = WORKSPACE / "inclawbate_state.json"
    if incl_path.exists():
        try:
            incl_raw = json.loads(incl_path.read_text(encoding="utf-8"))
            incl_data = incl_raw.get("data", {})
            staking = incl_data.get("staking", {})
            tvl_usd = staking.get("tvl_usd", 0)
            total_stakers = staking.get("total_stakers", 0)
            incl_state = {
                "tvl_usd": tvl_usd,
                "total_stakers": total_stakers,
            }
            # Crude status classification
            if tvl_usd and total_stakers:
                incl_status = "ok"
            else:
                incl_status = "observe"
        except Exception:
            incl_status = "unknown"

    # Load attention map and compute domain tensions
    attention_map = load_attention_map()

    domains = [
        {
            "label": "Sentinel / Gateway",
            "key": "ops",
            "status": "FAIL" if (gateway["status"] != "ok" or sentinel["status"] != "ok") else "OK",
            "reason": "gateway or sentinel not fully healthy" if (gateway["status"] != "ok" or sentinel["status"] != "ok") else "core ops healthy",
            "tension": max(domain_tension("gateway", attention_map), domain_tension("sentinel", attention_map)),
        },
        {
            "label": "Inclawbate / DeFi",
            "key": "inclawbate",
            "status": incl_status.upper(),
            "reason": f"staking tvl_usd={incl_state.get('tvl_usd', 0)}, stakers={incl_state.get('total_stakers', 0)}",
            "tension": domain_tension("inclawbate", attention_map),
        },
        {
            "label": "Cron / Automation",
            "key": "cron",
            "status": "OK" if cron["status"] == "ok" else "WARN",
            "reason": "openclaw cron list accessible" if cron["status"] == "ok" else "cron list output empty or error",
            "tension": domain_tension("cron", attention_map),
        },
    ]

    # Sort by tension descending
    domains.sort(key=lambda d: -d["tension"])

    print("OPS INBOX (tension-aware top 3)\n")
    for i, d in enumerate(domains[:3], start=1):
        print(f"{i}) [{d['status']}] {d['label']}")
        print(f"   - Reason: {d['reason']}")
        print(f"   - Tension: {d['tension']:.2f}\n")

    # Brief raw details
    print("Details:")
    print("- Gateway status snippet:")
    print(gateway["raw"])
    print("\n- Sentinel /health:")
    print(json.dumps(sentinel.get("health", {}), indent=2))
    print("\n- Sentinel log tail:")
    print(sentinel.get("log_tail", ""))
    print("\n- Cron list snippet:")
    print(cron["raw"])

    # Structured state
    state = {
        "timestamp": ts,
        "gateway": gateway["status"],
        "sentinel": sentinel["status"],
        "cron": cron["status"],
        "inclawbate": incl_status,
    }
    write_state(state)


if __name__ == "__main__":
    main()
