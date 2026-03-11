#!/usr/bin/env python3
import json
import time
from pathlib import Path
from datetime import datetime

LOG_FILE = Path('/home/thera/.openclaw/workspace/sentinel.log')
STATE_FILE = Path('/home/thera/.openclaw/workspace/sentinel_state.json')

SUMMARY_THRESHOLD_TOKEN = 150000  # 75% of TPM limit
SUMMARY_THRESHOLD_LATENCY_MS = 300  # example threshold


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def main():
    state = load_state()
    # Collect basic info
    now = datetime.utcnow().isoformat() + 'Z'
    token_usage = 0
    latency = None
    model_switches = 0
    gateway_health = 'Unknown'
    # Parse logs for recent info
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            logs = f.read()
        # Count token usages and latency
        token_usage = logs.count('tokens')
        latency_candidates = [int(line.split()[5].replace('ms','')) for line in logs.splitlines() if 'latency' in line]
        if latency_candidates:
            latency = max(latency_candidates)
        # Count model switches or events
        model_switches = logs.count('Model')
        # Check gateway health
        if 'gateway' in logs:
            gateway_health = 'Healthy' if 'ok' in logs else 'Unreachable'
    # Print summary
    print(f"--- Basic System Status @ {now} ---")
    print(f"Gateway status: {gateway_health}")
    print(f"Token usage in logs: {token_usage}")
    print(f"Max latency: {latency} ms")
    print(f"Model switches recorded: {model_switches}")
    # Alert if thresholds exceeded
    if token_usage > SUMMARY_THRESHOLD_TOKEN:
        print('ALERT: Token usage high')
    if latency and latency > SUMMARY_THRESHOLD_LATENCY_MS:
        print('ALERT: Latency high')

if __name__ == '__main__':
    main()
