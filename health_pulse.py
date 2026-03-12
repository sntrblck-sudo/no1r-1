#!/usr/bin/env python3
import json
import time
from datetime import datetime
from pathlib import Path
import urllib.request

ROOT = Path(__file__).parent
STATE_DIR = ROOT
PENDING = STATE_DIR / '.pending_alerts.json'

SENTINEL_HEALTH = 'http://127.0.0.1:18799/health'
GATEWAY_STATUS = 'http://127.0.0.1:18789/api/status'


def fetch_json(url, timeout=5):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def queue_alert(msg, t="health"):
    try:
        if PENDING.exists():
            with open(PENDING) as f:
                arr = json.load(f)
        else:
            arr = []
        arr.append({"type": t, "message": msg, "timestamp": datetime.utcnow().isoformat() + 'Z'})
        arr = arr[-20:]
        with open(PENDING, 'w') as f:
            json.dump(arr, f, indent=2)
    except Exception:
        pass


def main():
    s = fetch_json(SENTINEL_HEALTH)
    g = fetch_json(GATEWAY_STATUS)

    lines = []
    if isinstance(s, dict):
        lines.append(f"sentinel: failures={s.get('failures')} restarts={s.get('restarts')} cost=${s.get('cost_today'):.4f}")
        lines.append(f"model={s.get('model_tier')} heal_blocked={s.get('heal_permission_blocked')}")
    else:
        lines.append(f"sentinel: error fetching")

    if isinstance(g, dict):
        status = g.get('status', 'unknown')
        latency = g.get('latency_ms') if 'latency_ms' in g else None
        lines.append(f"gateway: {status} latency={latency}ms")
    else:
        lines.append("gateway: error fetching")

    msg = " | ".join(lines)
    # record event in log (append to sentinel.log as EVENT)
    try:
        log_line = {"ts": datetime.utcnow().isoformat() + 'Z', "type": "health_pulse", "summary": msg}
        with open(ROOT / 'sentinel.log', 'a') as f:
            f.write('EVENT ' + json.dumps(log_line) + '\n')
    except Exception:
        pass

    # queue alert for Telegram delivery
    queue_alert(msg, 'health_pulse')


if __name__ == '__main__':
    main()
