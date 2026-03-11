#!/usr/bin/env python3
"""
Safety Metrics Checker
Quick status check for router switching and safety metrics.
Updates ops_state.json and prints summary.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

STATE_FILE = Path(__file__).parent / "sentinel_state.json"
OPS_STATE_FILE = Path(__file__).parent / "ops_state.json"
GATEWAY_URL = "http://localhost:18789"
HEALTH_PORT = 18799


def check_gateway():
    """Check gateway health"""
    try:
        req = urllib.request.Request(f"{GATEWAY_URL}/health")
        r = urllib.request.urlopen(req, timeout=5)
        return "ok", r.status == 200
    except urllib.error.URLError as e:
        return "down", False
    except Exception as e:
        return "unknown", False


def check_sentinel():
    """Check Sentinel health server"""
    try:
        req = urllib.request.Request(f"http://localhost:{HEALTH_PORT}/health")
        r = urllib.request.urlopen(req, timeout=5)
        data = json.loads(r.read().decode())
        return "running", data
    except:
        return "inactive", None


def load_sentinel_state():
    """Load sentinel_state.json if exists"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return None


def update_ops_state(gateway_status, sentinel_status, sentinel_data, sentinel_state):
    """Update ops_state.json with current metrics"""
    now = datetime.utcnow().isoformat() + "Z"
    
    ops = {
        "gateway": gateway_status[0],
        "sentinel": sentinel_status[0],
        "last_check": now,
        "safety_metrics": {
            "cost_today": 0,
            "cost_threshold": 1.00,
            "cost_pct": 0,
            "gateway_failures": 0,
            "heal_blocked": False,
            "latency_avg_ms": None,
            "latency_spike": False
        },
        "alerts_24h": {
            "cost": 0,
            "health": 0,
            "latency": 0
        }
    }
    
    if sentinel_data:
        ops["safety_metrics"]["cost_today"] = sentinel_data.get("cost_today", 0)
        ops["safety_metrics"]["gateway_failures"] = sentinel_data.get("failures", 0)
    
    if sentinel_state:
        ops["safety_metrics"]["cost_threshold"] = sentinel_state.get("cost_threshold", 1.00)
        ops["safety_metrics"]["heal_blocked"] = sentinel_state.get("heal_permission_blocked", False)
        
        cost_today = sum(sentinel_state.get("daily_costs", []))
        threshold = sentinel_state.get("cost_threshold", 1.00)
        ops["safety_metrics"]["cost_pct"] = round((cost_today / threshold) * 100, 1) if threshold > 0 else 0
        ops["safety_metrics"]["cost_today"] = round(cost_today, 4)
        
        latency_stats = sentinel_state.get("latency_stats", {})
        ops["safety_metrics"]["latency_avg_ms"] = round(latency_stats.get("avg", 0), 1) if latency_stats.get("avg") else None
    
    with open(OPS_STATE_FILE, "w") as f:
        json.dump(ops, f, indent=2)
    
    return ops


def print_status(ops):
    """Print human-readable status"""
    print("\n" + "="*50)
    print("◼️  SAFETY METRICS STATUS")
    print("="*50)
    
    # Gateway status
    gw = ops["gateway"]
    gw_icon = "✓" if gw == "ok" else "✗" if gw == "down" else "?"
    print(f"\n{gw_icon} Gateway: {gw}")
    
    # Sentinel status
    sn = ops["sentinel"]
    sn_icon = "✓" if sn == "running" else "○" if sn == "inactive" else "?"
    print(f"{sn_icon} Sentinel: {sn}")
    
    # Safety metrics
    m = ops["safety_metrics"]
    print(f"\n**Cost Safety**")
    print(f"  Today: ${m['cost_today']:.4f} / ${m['cost_threshold']:.2f} ({m['cost_pct']}%)")
    
    cost_status = "✓" if m["cost_pct"] < 50 else "⚠️" if m["cost_pct"] < 80 else "✗"
    print(f"  {cost_status} Budget status: {'SAFE' if m['cost_pct'] < 50 else 'WATCH' if m['cost_pct'] < 80 else 'CRITICAL'}")
    
    print(f"\n**Gateway Safety**")
    print(f"  Failures: {m['gateway_failures']}")
    print(f"  Heal blocked: {m['heal_blocked']}")
    
    heal_status = "✓" if m["gateway_failures"] == 0 else "⚠️" if m["gateway_failures"] < 3 else "✗"
    print(f"  {heal_status} Health: {'OK' if m['gateway_failures'] == 0 else 'DEGRADED' if m['gateway_failures'] < 3 else 'CRITICAL'}")
    
    if m["latency_avg_ms"]:
        print(f"\n**Latency**")
        print(f"  Average: {m['latency_avg_ms']}ms")
        print(f"  Spike: {m['latency_spike']}")
    
    print(f"\n**Last check:** {ops['last_check']}")
    print("="*50 + "\n")


def main():
    print("Checking safety metrics...")
    
    gateway_status = check_gateway()
    sentinel_status, sentinel_data = check_sentinel()
    sentinel_state = load_sentinel_state()
    
    ops = update_ops_state(gateway_status, sentinel_status, sentinel_data, sentinel_state)
    print_status(ops)
    
    # Return exit code based on status
    if ops["gateway"] == "down":
        exit(2)
    elif ops["safety_metrics"]["gateway_failures"] >= 3 or ops["safety_metrics"]["cost_pct"] >= 80:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
