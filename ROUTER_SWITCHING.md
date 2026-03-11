# Router Switching & Safety Metrics

## Gateway Health Stack

**Priority order:**
1. **Primary** — `GATEWAY_URL` (default: `http://localhost:18789`)
2. **Alt** — `ALT_GATEWAY_URL` (default: `http://localhost:18789`)
3. **Fallback** — `OPENROUTER_FALLBACK` (`https://openrouter.ai/api/v1`)

**Health check:** `GET /health` with 10s timeout

---

## Safety Metrics (Tracked in `sentinel_state.json`)

### Cost Safety
| Metric | Default | Learned | Description |
|--------|---------|---------|-------------|
| `cost_threshold` | `$1.00/day` | Auto-adjusted | Daily spending limit |
| `model_switch_pct` | 70% | Yes | Switch to cheap model at X% of budget |
| `alert_pct` | 50% | Yes | Send cost alert at X% of budget |

**Cheap model cascade:**
```
1. openai/gpt-4o-mini ($0.15/$0.60 per 1M)
2. anthropic/claude-3-haiku ($0.25/$1.25)
3. google/gemini-flash-1.5 ($0.075/$0.30)
4. qwen/qwen-2.5-7b-instruct ($0.08/$0.08)
5. meta-llama/llama-3.2-1b-instruct ($0.05/$0.10)
```

### Gateway Safety
| Metric | Threshold | Action |
|--------|-----------|--------|
| `failures` | ≥3 | Proactive restart |
| `heal_permission_blocked` | true | Stop heal attempts, alert once |
| `last_heal_alert` | 1h throttle | Prevent alert spam |

**Healing methods (ordered by preference):**
1. `kill_gateway` — pkill + systemctl start
2. `restart_service` — systemctl restart

**Recovery behavior (G3):**
- When gateway becomes healthy again → reset `failures` to 0, clear `last_heal_alert`

### Latency Safety
| Metric | Calculation | Alert |
|--------|-------------|-------|
| `latency_stats.avg` | Rolling 50 samples | — |
| `spike_threshold` | max(200ms, avg × 4) | Alert if current > threshold |

**Purpose:** Predictive failure detection — latency spikes often precede gateway crashes.

### Resource Safety
| Metric | Threshold | Alert |
|--------|-----------|-------|
| Disk usage | ≥80% | Queue health alert |
| Memory usage | ≥90% | Queue health alert |

---

## Alert Throttling (A1, A3)

**Cost alerts:**
- Learned threshold (default 50%) — once per threshold
- Hard thresholds: 80%, 90%, 100% — once each
- Reset daily

**Health alerts:**
- Heal failures — max once per hour
- Permission blocked — once (until manual reset)
- Latency spikes — debounced via spike_threshold

---

## Learning System

**What gets learned:**
1. **Method preferences** — Which heal method works best (`success/total` per method)
2. **Threshold tuning** — Adjust `model_switch_pct`, `alert_pct` based on outcomes
3. **Cost threshold** — Auto-lower if consistently <50% of budget for 7 days

**Update cadence:**
- Method preferences: Every heal attempt
- Thresholds: Daily learning update
- Cost threshold: Daily (if under 50% for 7 days, reduce by 10%)

---

## State File: `sentinel_state.json`

```json
{
  "pid": 12345,
  "started": "2026-03-10T19:00:00Z",
  "restarts": 2,
  "failures": 0,
  "last_learning_update": "2026-03-10T19:00:00Z",
  "cost_threshold": 1.00,
  "daily_costs": [0.0023, 0.0018, ...],
  "current_model": "default",
  "model_tier": "default",
  "method_preferences": {
    "heal_gateway": {
      "kill_gateway": {"success": 5, "total": 6},
      "restart_service": {"success": 2, "total": 3}
    },
    "cheap_model": {
      "openai/gpt-4o-mini": {"success": 10, "total": 10}
    }
  },
  "learned_thresholds": {
    "model_switch_pct": {"samples": [...], "best": 65},
    "alert_pct": {"samples": [...], "best": 45},
    "proactive_restart_failures": {"samples": [...], "best": 3}
  },
  "heal_permission_blocked": false,
  "last_heal_alert": null,
  "latency_stats": {
    "samples": [45, 52, 48, ...],
    "spike_threshold": 200,
    "avg": 47.5
  }
}
```

---

## HTTP Endpoints (Port 18799)

- `GET /health` — Summary status (status, uptime, failures, restarts, cost_today)
- `GET /status` — Full state JSON

---

## Operational Principles

**G1. Boring is success** — Stable gateway + stable sentinel = no changes needed

**G2. Heal vs. Permission** — If systemd denies restarts, mark `heal_permission_blocked` and stop hammering

**G3. Reset on recovery** — Healthy gateway = reset failures, clear stale alerts

**O1. One small change** — Modify one metric/threshold at a time; track causality

---

## To Activate Sentinel

```bash
# Set environment (optional — defaults shown)
export GATEWAY_URL="http://localhost:18789"
export ALT_GATEWAY_URL="http://localhost:18789"
export MAX_COST_PER_DAY="1.00"
export CHECK_INTERVAL="300"

# Run
python3 sentinel.py

# Or as systemd service
sudo cp sentinel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sentinel
```

**Check status:**
```bash
curl http://localhost:18799/health
curl http://localhost:18799/status
tail -20 sentinel.log
```
