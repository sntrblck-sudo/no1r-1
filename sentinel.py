#!/usr/bin/env python3
"""
Sentinel - Autonomous Agent v2
Self-healing, learning, 7-day unsupervised operation
"""

import json
import os
import sys
import time
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

STATE_FILE = Path(__file__).parent / "sentinel_state.json"
LOG_FILE = Path(__file__).parent / "sentinel.log"

# Graceful shutdown handler
import signal

def signal_handler(signum, frame):
    log(f"Received signal {signum}, shutting down...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Config
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:18789")
ALT_GATEWAY_URL = os.environ.get("ALT_GATEWAY_URL", "http://localhost:18789")
OPENROUTER_FALLBACK = os.environ.get("OPENROUTER_FALLBACK", "https://openrouter.ai/api/v1")
MAX_COST_PER_DAY = float(os.environ.get("MAX_COST_PER_DAY", "1.00"))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "300"))  # 5 min
MAX_LOG_SIZE_MB = 10
MAX_LOG_FILES = 5

# Cheap fallback models (ordered by price, cheapest first)
CHEAP_MODELS = [
    "openai/gpt-4o-mini",
    "openai/gpt-4o-mini-2024-07-18",
    "anthropic/claude-3-haiku",
    "google/gemini-flash-1.5",
    "mistralai/mistral-7b-instruct",
    # New additions (tested)
    "deepseek/deepseek-chat",
    "qwen/qwen-2.5-7b-instruct",
    "meta-llama/llama-3.2-1b-instruct",
    "google/gemma-2-2b-it",
]

# Model pricing (per 1M tokens) - approximate
MODEL_PRICING = {
    # OpenAI
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
    "openai/gpt-5.1-codex-mini": {"input": 1.25, "output": 5.00},
    # Anthropic
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    # Google
    "google/gemini-flash-1.5": {"input": 0.075, "output": 0.30},
    "google/gemini-pro-1.5": {"input": 1.25, "output": 5.00},
    "google/gemma-2-2b-it": {"input": 0.10, "output": 0.10},
    # Mistral
    "mistralai/mistral-7b-instruct": {"input": 0.20, "output": 0.20},
    "mistralai/mistral-small": {"input": 0.30, "output": 0.30},
    # DeepSeek
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    # Qwen (Alibaba)
    "qwen/qwen-2.5-7b-instruct": {"input": 0.08, "output": 0.08},
    # Meta
    "meta-llama/llama-3.2-1b-instruct": {"input": 0.05, "output": 0.10},
}


def estimate_request_cost(model, input_tokens=1000, output_tokens=500):
    """Estimate cost of an API request based on model and token counts"""
    pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 4.0})  # Default conservative estimate
    
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    
    return input_cost + output_cost


def track_cost(state, model, input_tokens=1000, output_tokens=500):
    """Add cost to daily total"""
    cost = estimate_request_cost(model, input_tokens, output_tokens)
    
    if "daily_costs" not in state:
        state["daily_costs"] = []
    
    state["daily_costs"].append(cost)
    
    # Keep only last 24 hours worth (assuming hourly checks)
    if len(state["daily_costs"]) > 24:
        state["daily_costs"] = state["daily_costs"][-24:]
    
    return state


def log(msg):
    timestamp = datetime.utcnow().isoformat() + "Z"
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if log needs rotation
    if LOG_FILE.exists():
        try:
            size_mb = LOG_FILE.stat().st_size / (1024 * 1024)
            if size_mb >= MAX_LOG_SIZE_MB:
                rotate_logs(LOG_FILE)
        except:
            pass
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
            f.flush()
    except:
        pass



def rotate_logs(log_path):
    """Rotate log files"""
    import shutil
    
    log_path = Path(log_path)
    base = log_path.stem
    ext = log_path.suffix
    parent = log_path.parent
    
    # Remove oldest if at max
    oldest = parent / f"{base}.{MAX_LOG_FILES}{ext}"
    if oldest.exists():
        oldest.unlink()
    
    # Shift others
    for i in range(MAX_LOG_FILES - 1, 0, -1):
        src = parent / f"{base}.{i}{ext}"
        dst = parent / f"{base}.{i+1}{ext}"
        if src.exists():
            shutil.move(str(src), str(dst))
    
    # Rename current to .1
    if log_path.exists():
        shutil.move(str(log_path), str(parent / f"{base}.1{ext}"))
    
    log(f"Log rotated (max {MAX_LOG_SIZE_MB}MB)")


def queue_alert(message, alert_type="custom"):
    """Queue an alert for Telegram"""
    alert_file = STATE_FILE.parent / ".pending_alerts.json"
    
    try:
        # Read existing
        if alert_file.exists():
            with open(alert_file) as f:
                alerts = json.load(f)
        else:
            alerts = []
        
        # Add new
        alerts.append({
            "type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Keep only last 10
        alerts = alerts[-10:]
        
        # Write back
        with open(alert_file, "w") as f:
            json.dump(alerts, f)
    
    except Exception as e:
        log(f"Failed to queue alert: {e}")


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
        
        # Merge in any new default keys (for schema updates)
        defaults = {
            "method_preferences": {},
            "learned_thresholds": {
                "model_switch_pct": 70,
                "alert_pct": 50,
                "proactive_restart_failures": 3,
            },
        }
        for key, default_val in defaults.items():
            if key not in state:
                state[key] = default_val
        
        return state
    
    return {
        "started": datetime.utcnow().isoformat() + "Z",
        "pid": os.getpid(),
        "restarts": 0,
        "failures": 0,
        "last_learning_update": datetime.utcnow().isoformat() + "Z",
        "method_preferences": {},
        "cost_threshold": MAX_COST_PER_DAY,
        "daily_costs": [],
        "current_model": "default",
        "model_tier": "default",
        "learned_thresholds": {
            "model_switch_pct": 70,
            "alert_pct": 50,
            "proactive_restart_failures": 3,
        },
        # Heal behaviour flags
        "heal_permission_blocked": False,
        "last_heal_alert": None,
    }


# Health check HTTP server (runs in background thread)
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            state = load_state()
            started = state.get("started", "")
            try:
                uptime = str(datetime.utcnow() - datetime.fromisoformat(started.replace("Z", "+00:00")))
            except:
                uptime = "unknown"
            resp = {
                "status": "ok" if state.get("pid") else "no pid",
                "uptime": uptime,
                "failures": state.get("failures", 0),
                "restarts": state.get("restarts", 0),
                "cost_today": sum(state.get("daily_costs", []))
            }
            self.wfile.write(json.dumps(resp).encode())
        elif self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            state = load_state()
            self.wfile.write(json.dumps(state, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def start_health_server(port=18799):
    try:
        server = HTTPServer(("", port), HealthHandler)
        log(f"Health server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        log(f"Health server failed: {e}")

# Start health server in background
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_gateway_usage():
    """Get current API usage from gateway"""
    try:
        req = urllib.request.Request(f"{GATEWAY_URL}/api/status")
        r = urllib.request.urlopen(req, timeout=10)
        data = json.loads(r.read().decode())
        return data
    except:
        return None


def should_use_cheap_model(state):
    """Decide if we should switch to cheaper model"""
    # If already on cheap/emergency, stay there
    if state.get("model_tier") in ["cheap", "emergency"]:
        return True
    
    # Check daily costs
    today_cost = sum(state.get("daily_costs", []))
    daily_limit = state.get("cost_threshold", MAX_COST_PER_DAY)
    
    # Use learned threshold (default 70%)
    switch_pct = get_learned_threshold(state, "model_switch_pct", 70)
    
    # If we've used X%+ of daily budget, switch to cheap
    if daily_limit > 0 and today_cost >= daily_limit * (switch_pct / 100):
        log(f"Daily budget {today_cost:.2f}/{daily_limit:.2f} ({switch_pct}%), switching to cheap model")
        return True
    
    # Check gateway usage if available
    usage = get_gateway_usage()
    if usage:
        # Could add more logic here based on active sessions, etc.
        pass
    
    return False


def get_cheap_model_index(state):
    """Get next cheap model to try (cycles through)"""
    prefs = state.get("method_preferences", {})
    model_prefs = prefs.get("cheap_model", {})
    
    # Find model with best success rate
    best_model = None
    best_rate = 0
    
    for model, stats in model_prefs.items():
        if stats.get("total", 0) >= 1:
            rate = stats.get("success", 0) / stats["total"]
            if rate > best_rate:
                best_rate = rate
                best_model = model
    
    if best_model:
        return best_model
    
    # Default to first cheap model
    return CHEAP_MODELS[0]


# Track tested models
_tested_models = {}


def test_model_safe(model, timeout=10):
    """Safely test if a model responds (read-only check)"""
    global _tested_models
    
    if model in _tested_models:
        return _tested_models[model]
    
    # For now, just verify the model is in our pricing list
    # Full API testing would require actual API key with credits
    if model in MODEL_PRICING:
        _tested_models[model] = True
        return True
    
    _tested_models[model] = False
    return False


def record_model_outcome(state, model, success):
    """Track cheap model success/failure"""
    if "method_preferences" not in state:
        state["method_preferences"] = {}
    if "cheap_model" not in state["method_preferences"]:
        state["method_preferences"]["cheap_model"] = {}
    
    if model not in state["method_preferences"]["cheap_model"]:
        state["method_preferences"]["cheap_model"][model] = {"success": 0, "total": 0}
    
    stats = state["method_preferences"]["cheap_model"][model]
    stats["total"] += 1
    if success:
        stats["success"] += 1
    
    return state


# Track which alerts we've sent (to avoid spam)
_alerts_sent = {"50": False, "80": False, "90": False, "100": False}


def check_usage_alerts(state):
    """Check usage and send alerts at thresholds"""
    global _alerts_sent
    
    today_cost = sum(state.get("daily_costs", []))
    daily_limit = state.get("cost_threshold", MAX_COST_PER_DAY)
    
    if daily_limit <= 0:
        return state, today_cost
    
    pct = (today_cost / daily_limit) * 100
    
    # Use learned alert threshold (default 50%)
    alert_pct = get_learned_threshold(state, "alert_pct", 50)
    
    # Alert at learned threshold
    key = str(int(alert_pct))
    if pct >= alert_pct and not _alerts_sent.get(key):
        msg = f"⚠️ COST ALERT: {pct:.1f}% of daily budget used (${today_cost:.2f}/${daily_limit:.2f})"
        log(msg)
        queue_alert(msg, "cost")
        _alerts_sent[key] = True
        # Record outcome - alert was sent (success = user responded/acknowledged)
        # For now, track that we alerted
    
    # Also alert at 80%, 90%, 100% regardless (critical thresholds)
    for threshold in [80, 90, 100]:
        key = str(threshold)
        if pct >= threshold and not _alerts_sent.get(key):
            msg = f"⚠️ COST ALERT: {pct:.1f}% of daily budget used (${today_cost:.2f}/${daily_limit:.2f})"
            log(msg)
            queue_alert(msg, "cost")
            _alerts_sent[key] = True
    
    # Reset alerts if new day
    last_update = state.get("last_learning_update", "")
    if last_update:
        last_date = last_update[:10]
        today = datetime.utcnow().isoformat()[:10]
        if last_date != today:
            _alerts_sent = {"50": False, "80": False, "90": False, "100": False}
    
    return state, today_cost


# Track total requests for cost estimation
_request_count = 0
_last_session_check = None


def get_recent_session_count():
    """Count sessions from last N minutes"""
    import glob
    
    sessions_dir = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
    if not sessions_dir.exists():
        return 0
    
    now = datetime.utcnow()
    count = 0
    
    for f in sessions_dir.glob("*.jsonl"):
        try:
            # Check file modification time
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if (now - mtime).total_seconds() < 600:  # Last 10 minutes
                count += 1
        except:
            pass
    
    return count


def simulate_activity(state):
    """Estimate API activity based on actual session activity"""
    global _request_count, _last_session_check
    
    _request_count += 1
    
    # Get actual session activity
    active_sessions = get_recent_session_count()
    
    # If there are active sessions, estimate real usage
    # Each session likely generates ~1-3 API calls per check interval
    if active_sessions > 0:
        # More accurate estimation based on active sessions
        requests_this_cycle = active_sessions * 2  # 2 requests per active session
    else:
        requests_this_cycle = 0
    
    # Only track if there was actual activity
    if requests_this_cycle > 0:
        model = state.get("current_model", "default")
        if model == "default":
            model = "openai/gpt-5.1-codex-mini"
        
        # Average tokens per request
        import random
        input_tok = random.randint(800, 2000)
        output_tok = random.randint(400, 1200)
        
        # Track each request
        for _ in range(requests_this_cycle):
            state = track_cost(state, model, input_tok, output_tok)
    
    return state


def check_gateway(url):
    try:
        req = urllib.request.Request(f"{url}/health")
        r = urllib.request.urlopen(req, timeout=10)
        return r.status == 200, url
    except:
        return False, url


def check_gateway_health():
    """Check primary, then alt, then fallback"""
    ok, url = check_gateway(GATEWAY_URL)
    if ok:
        return True, url, "primary"
    
    log(f"Primary gateway failed, trying alt...")
    ok, url = check_gateway(ALT_GATEWAY_URL)
    if ok:
        return True, url, "alt"
    
    log(f"Alt gateway also failed")
    return False, None, "none"


def get_gateway_latency(url):
    try:
        start = time.time()
        req = urllib.request.Request(f"{url}/health")
        r = urllib.request.urlopen(req, timeout=5)
        latency = (time.time() - start) * 1000
        return latency, r.status == 200
    except:
        return None, False


# Latency tracking for pattern learning
_latency_history = []

def record_latency(state, latency):
    """Track latency for pattern learning"""
    global _latency_history
    
    if latency is None:
        return state
    
    _latency_history.append({"latency": latency, "timestamp": datetime.utcnow().isoformat()})
    _latency_history = _latency_history[-100:]  # Keep last 100
    
    # Initialize latency tracking in state
    if "latency_stats" not in state:
        state["latency_stats"] = {"samples": [], "spike_threshold": 500, "avg": None}
    
    stats = state["latency_stats"]
    stats["samples"].append(latency)
    stats["samples"] = stats["samples"][-50:]  # Keep last 50
    
    # Calculate average
    if stats["samples"]:
        stats["avg"] = sum(stats["samples"]) / len(stats["samples"])
        
        # Learn spike threshold: if latency > 4x avg AND > 200ms, that's a spike
        # Much less sensitive - only major issues trigger alerts
        if stats["avg"] > 0:
            stats["spike_threshold"] = max(200, stats["avg"] * 4)
    
    return state


def check_latency_spike(state):
    """Check if current latency is a spike (predictive failure)"""
    stats = state.get("latency_stats", {})
    current = _latency_history[-1]["latency"] if _latency_history else None
    
    if not current or not stats.get("avg"):
        return False
    
    threshold = stats.get("spike_threshold", 500)
    return current > threshold


def record_outcome(state, action, method, success):
    """Learning: track success/failure per action-method pair"""
    if action not in state["method_preferences"]:
        state["method_preferences"][action] = {}
    
    if method not in state["method_preferences"][action]:
        state["method_preferences"][action][method] = {"success": 0, "total": 0}
    
    stats = state["method_preferences"][action][method]
    stats["total"] += 1
    if success:
        stats["success"] += 1
    
    state["last_learning_update"] = datetime.utcnow().isoformat() + "Z"
    return state


def get_preferred_method(state, action):
    """Get method with highest success rate"""
    if action not in state["method_preferences"]:
        return None
    
    methods = state["method_preferences"][action]
    best = None
    best_rate = 0
    
    for method, stats in methods.items():
        if stats["total"] >= 2:  # Minimum samples
            rate = stats["success"] / stats["total"]
            if rate > best_rate:
                best_rate = rate
                best = method
    
    return best


def record_threshold_outcome(state, threshold_name, value, success):
    """Learn from threshold decisions"""
    if "learned_thresholds" not in state:
        state["learned_thresholds"] = {}
    
    entry = state["learned_thresholds"].get(threshold_name)
    
    # Handle old format (int) - convert to new format
    if entry is None or isinstance(entry, int):
        state["learned_thresholds"][threshold_name] = {"samples": [], "best": value}
        entry = state["learned_thresholds"][threshold_name]
    
    entry["samples"].append({"value": value, "success": success})
    
    # Keep last 20 samples
    entry["samples"] = entry["samples"][-20:]
    
    # Adjust if this value led to failure
    if not success and threshold_name == "model_switch_pct":
        # If switching failed, maybe we switched too late - lower threshold
        entry["best"] = max(30, entry["best"] - 5)
    elif not success and threshold_name == "alert_pct":
        # If alert didn't help, maybe alert earlier
        entry["best"] = max(20, entry["best"] - 10)
    
    state["last_learning_update"] = datetime.utcnow().isoformat() + "Z"
    return state


def get_learned_threshold(state, threshold_name, default):
    """Get best threshold from learning"""
    if "learned_thresholds" not in state:
        return default
    
    entry = state["learned_thresholds"].get(threshold_name, {})
    
    # Handle both old format (int) and new format (dict)
    if isinstance(entry, int):
        return entry
    if isinstance(entry, dict):
        return entry.get("best", default)
    
    return default


def heal_gateway(state):
    """Attempt to restart gateway in a permission-aware way"""
    action = "heal_gateway"

    # Try preferred method first
    preferred = get_preferred_method(state, action)
    methods = ["kill_gateway", "restart_service"]

    if preferred in methods:
        methods.remove(preferred)
        methods.insert(0, preferred)

    permission_blocked = False

    for method in methods:
        log(f"Attempting heal via {method}...")
        success = False

        if method == "kill_gateway":
            try:
                # Find and kill gateway process, then restart via systemd
                rc_kill = os.system("pkill -f 'openclaw-gateway'")
                time.sleep(2)
                rc_start = os.system("systemctl start openclaw-gateway")
                time.sleep(5)
                ok, _, _ = check_gateway_health()
                success = ok

                # Detect permission issues from systemctl
                if rc_start != 0:
                    permission_blocked = True
            except Exception as e:
                log(f"kill_gateway failed: {e}")

        elif method == "restart_service":
            try:
                rc_restart = os.system("systemctl restart openclaw-gateway")
                time.sleep(5)
                ok, _, _ = check_gateway_health()
                success = ok

                # Detect permission issues from systemctl
                if rc_restart != 0:
                    permission_blocked = True
            except Exception as e:
                log(f"restart_service failed: {e}")

        state = record_outcome(state, action, method, success)

        if success:
            log(f"Heal succeeded via {method}")
            state["restarts"] += 1
            return state, True

    # If we got here, all methods failed
    state["failures"] += 1

    if permission_blocked:
        log("Heal failed due to permission issues with systemctl; disabling further heal attempts until manual reset")
        state["heal_permission_blocked"] = True
        queue_alert(
            "⚠️ Sentinel could not restart openclaw-gateway due to permission requirements. Heal attempts disabled until manual intervention.",
            "health",
        )

    return state, False


def daily_learning_update(state):
    """Analyze patterns and adjust thresholds"""
    log("Running daily learning update...")
    
    # Check if cost threshold needs adjustment
    if state["daily_costs"]:
        recent = sum(state["daily_costs"][-7:])  # Last 7 days
        if recent < state["cost_threshold"] * 0.5:
            # Consistently under budget, lower threshold slightly
            state["cost_threshold"] = max(0.10, state["cost_threshold"] * 0.9)
            log(f"Lowered cost threshold to ${state['cost_threshold']:.2f}")
    
    state["last_learning_update"] = datetime.utcnow().isoformat() + "Z"
    return state


def heartbeat(state):
    """Hourly heartbeat with metrics"""
    ok, url, tier = check_gateway_health()
    latency = None
    if ok:
        latency, _ = get_gateway_latency(url)
    
    # Record latency for learning
    if latency:
        state = record_latency(state, latency)
    
    # Check for latency spike (predictive)
    if latency and check_latency_spike(state):
        log(f"⚠️ Latency spike detected: {latency}ms (avg={state.get('latency_stats',{}).get('avg',0):.0f}ms)")
        queue_alert(f"⚠️ Latency spike: {latency:.0f}ms", "health")
    
    # Resource monitoring (disk/memory) - using shell commands
    try:
        # Check disk usage
        disk_pct = int(os.popen("df / | tail -1 | awk '{print $5}' | sed 's/%//'").read().strip())
        if disk_pct >= 80:
            queue_alert(f"⚠️ Disk at {disk_pct}%", "health")
        
        # Check memory usage
        mem_pct = int(os.popen("free | grep Mem | awk '{print int($3/$2*100)}'").read().strip())
        if mem_pct >= 90:
            queue_alert(f"⚠️ Memory at {mem_pct}%", "health")
    except Exception:
        pass  # Skip if commands fail
    
    log(f"Heartbeat: gateway={tier} latency={latency}ms failures={state['failures']} restarts={state['restarts']}")
    return state


def main():
    log("=== Sentinel v2 Starting ===")
    state = load_state()

    # Singleton guard: if a previous Sentinel PID is still running, exit
    prev_pid = state.get("pid")
    if prev_pid and prev_pid != os.getpid():
        try:
            os.kill(prev_pid, 0)  # Check if process exists
        except OSError:
            # Old PID is dead, safe to continue
            pass
        else:
            log(f"Existing Sentinel instance detected (pid={prev_pid}), exiting")
            return

    state["pid"] = os.getpid()
    state["started"] = datetime.utcnow().isoformat() + "Z"
    save_state(state)
    
    last_heartbeat = datetime.utcnow()
    last_daily = datetime.utcnow()
    last_learning = datetime.utcnow()
    
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            
            # Log alive every 12 cycles (1 hour)
            if loop_count % 12 == 0:
                log(f"Alive: loop {loop_count}")
            
            now = datetime.utcnow()
            
            # Health check with timeout protection
            ok, url, tier = check_gateway_health()

            # If gateway is healthy again, reset failure counter and heal alerts
            if ok and state.get("failures", 0) > 0:
                log(f"Gateway healthy again, resetting failures (was {state['failures']})")
                state["failures"] = 0
                state.pop("last_heal_alert", None)
            
            # Get latency and record for learning
            latency, _ = get_gateway_latency(url) if ok else (None, False)
            if latency:
                state = record_latency(state, latency)
                
                # Check for latency spike (predictive failure detection)
                if check_latency_spike(state):
                    log(f"⚠️ Latency spike: {latency}ms (avg={state.get('latency_stats',{}).get('avg',0):.0f}ms)")
                    queue_alert(f"⚠️ Latency spike: {latency:.0f}ms", "health")
            
            # Proactive restart: if we've had N failures, restart before complete failure
            if not ok:
                proactive_threshold = get_learned_threshold(state, "proactive_restart_failures", 3)
                if state.get("failures", 0) >= proactive_threshold:
                    log(f"Proactive restart triggered (failures={state['failures']})")
                    state, healed = heal_gateway(state)
                    if healed:
                        queue_alert("♻️ Proactive restart performed", "health")
            
            # Model cost management
            use_cheap = should_use_cheap_model(state)
            if use_cheap and state.get("model_tier") != "cheap":
                cheap_model = get_cheap_model_index(state)
                state["model_tier"] = "cheap"
                state["current_model"] = cheap_model
                log(f"Switched to cheap model: {cheap_model}")
                # Record model attempt
                state = record_model_outcome(state, cheap_model, ok)  # success = gateway healthy
            elif not use_cheap and state.get("model_tier") == "cheap":
                state["model_tier"] = "default"
                state["current_model"] = "default"
                log("Reverted to default model")
            
            # Simulate API activity for cost tracking
            state = simulate_activity(state)
            
            # Get session activity
            active_sessions = get_recent_session_count()
            
            # Usage alerts
            state, today_cost = check_usage_alerts(state)
            
            # Log cost only on hourly heartbeat
            if loop_count % 12 == 0:
                log(f"Cost: ${today_cost:.4f} / ${state.get('cost_threshold', MAX_COST_PER_DAY):.2f} | Sessions: {active_sessions}")
            
            if not ok:
                # Gateway unhealthy
                if state.get("heal_permission_blocked"):
                    # We already know heals are blocked by permissions; avoid spamming alerts
                    log("Gateway unhealthy, but heal is permission-blocked; skipping heal attempts")
                else:
                    log(f"Gateway unhealthy, attempting heal...")
                    state, healed = heal_gateway(state)
                    if not healed:
                        # Throttle heal-failed alerts to at most once per hour
                        now_iso = datetime.utcnow().isoformat() + "Z"
                        last_alert = state.get("last_heal_alert")
                        should_alert = True
                        if last_alert:
                            try:
                                last_dt = datetime.fromisoformat(last_alert.replace("Z", "+00:00"))
                                if datetime.utcnow() - last_dt < timedelta(hours=1):
                                    should_alert = False
                            except Exception:
                                # On parse error, treat as needing alert
                                should_alert = True
                        if should_alert:
                            log("WARNING: Heal failed, will retry next cycle")
                            queue_alert("⚠️ Gateway heal failed - manual intervention may be needed", "health")
                            state["last_heal_alert"] = now_iso
            
            # Hourly heartbeat
            if now - last_heartbeat > timedelta(hours=1):
                state = heartbeat(state)
                last_heartbeat = now
            
            # Daily learning update
            if now - last_daily > timedelta(days=1):
                state = daily_learning_update(state)
                last_daily = now
            
            save_state(state)
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Sentinel stopped by user")
            break
        except Exception as e:
            log(f"Error: {e}")
            state["failures"] += 1
            save_state(state)
            time.sleep(CHECK_INTERVAL)
    
    log("=== Sentinel v2 Exiting ===")


if __name__ == "__main__":
    main()
