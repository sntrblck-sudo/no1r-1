#!/usr/bin/env python3
"""
Curiosity Agent - Weekly research and insights
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
import urllib.parse

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
LOG_FILE = WORKSPACE / "curiosity.log"
STATE_FILE = WORKSPACE / "curiosity_state.json"

def log(msg):
    timestamp = datetime.utcnow().isoformat() + "Z"
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_run": None, "insights": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def check_clawhub():
    """Check for interesting new skills via CLI"""
    insights = []
    
    # Search queries to try
    queries = ["monitoring", "automation", "backup", "health", "productivity"]
    
    for query in queries[:3]:
        try:
            result = subprocess.run(
                ["clawhub", "search", query, "--limit", "2"],
                capture_output=True, text=True, timeout=15, cwd=str(WORKSPACE)
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip first line
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("-"):
                        # Format: "skill-name  Description  (score)"
                        parts = line.split()
                        if parts:
                            name = parts[0]
                            insights.append(f"Skill: {name}")
        except Exception as e:
            log(f"ClawHub search failed: {e}")
    
    return list(set(insights))[:5]  # Dedupe

def analyze_sentinel():
    """Analyze Sentinel's learned patterns"""
    insights = []
    
    state_file = WORKSPACE / "sentinel_state.json"
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)
        
        # Cost analysis
        daily_costs = state.get("daily_costs", [])
        if daily_costs:
            avg_cost = sum(daily_costs) / len(daily_costs)
            threshold = state.get("cost_threshold", 1.0)
            usage_pct = (avg_cost / threshold) * 100
            insights.append(f"Cost: Using {usage_pct:.1f}% of budget (${avg_cost:.4f}/day avg)")
        
        # Method preferences
        prefs = state.get("method_preferences", {})
        if prefs:
            for action, methods in prefs.items():
                for method, stats in methods.items():
                    total = stats.get("total", 0)
                    if total >= 3:
                        rate = stats.get("success", 0) / total * 100
                        insights.append(f"Learning: {action}/{method} = {rate:.0f}% ({total} samples)")
        
        # Latency
        lat_stats = state.get("latency_stats", {})
        if lat_stats.get("avg"):
            insights.append(f"Latency: avg={lat_stats['avg']:.0f}ms, spike threshold={lat_stats.get('spike_threshold', 0):.0f}ms")
    
    return insights

def check_system_health():
    """Quick system metrics"""
    insights = []
    
    # Disk
    try:
        result = subprocess.run("df / | tail -1 | awk '{print $5}'", shell=True, capture_output=True, text=True)
        disk = result.stdout.strip().replace("%", "")
        insights.append(f"Disk: {disk}% used")
    except:
        pass
    
    # Memory
    try:
        result = subprocess.run("free | grep Mem | awk '{print int($3/$2*100)}'", shell=True, capture_output=True, text=True)
        mem = result.stdout.strip()
        insights.append(f"Memory: {mem}% used")
    except:
        pass
    
    return insights

def main():
    log("=== Curiosity Agent Running ===")
    
    state = load_state()
    insights = []
    
    # Run research
    log("Analyzing Sentinel patterns...")
    insights.extend(analyze_sentinel())
    
    log("Checking system health...")
    insights.extend(check_system_health())
    
    log("Searching ClawHub...")
    try:
        insights.extend(check_clawhub())
    except Exception as e:
        log(f"ClawHub error: {e}")
    
    # Save insights
    state["last_run"] = datetime.utcnow().isoformat() + "Z"
    state["insights"] = insights
    save_state(state)
    
    # Report
    report = "◼️ Curiosity Report\n\n" + "\n".join(f"• {i}" for i in insights)
    log(report)
    print("\n" + report)
    
    log("=== Curiosity Agent Done ===")

if __name__ == "__main__":
    main()
