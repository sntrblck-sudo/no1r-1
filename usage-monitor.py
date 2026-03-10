#!/usr/bin/env python3
"""Usage monitor - switches model at 80% threshold"""
import subprocess
import json
import os

CONFIG_FILE = "/home/sntrblck/.openclaw/openclaw.json"
STATE_FILE = "/home/sntrblck/.openclaw/workspace/.usage-monitor-state.json"
THRESHOLD = 60  # Switch at 60% usage (40% remaining)

def get_usage():
    """Get current usage percentage from openclaw models status (text output)"""
    try:
        # Use text output to get usage percentage
        result = subprocess.run(
            ["openclaw", "models", "status"],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout
        
        # Look for openai-codex usage line like "usage: 5h 87% left"
        for line in output.split('\n'):
            if "openai-codex" in line.lower() and "% left" in line:
                # Extract percentage: "87% left" -> 13% used
                import re
                match = re.search(r'(\d+)% left', line)
                if match:
                    pct_left = int(match.group(1))
                    pct_used = 100 - pct_left
                    return pct_used, line.strip()
                    
        return None, "No openai-codex usage found in output"
    except Exception as e:
        return None, str(e)

def switch_to_gemma():
    """Switch default model to Gemma"""
    subprocess.run(
        ["openclaw", "models", "set", "openrouter/google/gemma-3-27b-it:free"],
        capture_output=True
    )
    return True

def main():
    pct_used, info = get_usage()
    
    if pct_used is None:
        print(f"Could not get usage: {info}")
        return
    
    print(f"Current usage: {pct_used}% (info: {info})")
    
    # Load state
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    
    # Check if already switched
    if state.get("switched", False):
        print("Already switched to Gemma, skipping")
        return
    
    if pct_used >= THRESHOLD:
        print(f"Usage {pct_used}% >= {THRESHOLD}%, switching to Gemma...")
        if switch_to_gemma():
            state["switched"] = True
            state["switched_at"] = str(pct_used)
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f)
            print("✓ Switched to gemma-3-27b-it:free")
        else:
            print("Failed to switch")
    else:
        print(f"Usage {pct_used}% < {THRESHOLD}%, no switch needed")

if __name__ == "__main__":
    main()
