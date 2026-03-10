#!/usr/bin/env python3
"""
Telegram Alert Bot - Send alerts to your phone
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# Config
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
LOG_FILE = Path(__file__).parent / "telegram_alerts.log"
CHECK_INTERVAL = int(os.environ.get("ALERT_CHECK_INTERVAL", "60"))  # 1 min


def log(msg):
    timestamp = datetime.utcnow().isoformat() + "Z"
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def send_message(text):
    """Send message via Telegram bot"""
    if not TOKEN or not CHAT_ID:
        return False, "Not configured"
    
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            if result.get("ok"):
                return True, "Sent"
            else:
                return False, result.get("description", "Unknown error")
    
    except Exception as e:
        return False, str(e)


def read_alerts():
    """Read pending alerts from file"""
    alert_file = Path(__file__).parent / ".pending_alerts.json"
    
    if not alert_file.exists():
        return []
    
    try:
        with open(alert_file) as f:
            return json.load(f)
    except:
        return []


def clear_alerts():
    """Clear processed alerts (simple: delete the file)."""
    alert_file = Path(__file__).parent / ".pending_alerts.json"
    try:
        if alert_file.exists():
            alert_file.unlink()
    except Exception:
        # If we can't delete, degrade gracefully
        try:
            with open(alert_file, "w") as f:
                json.dump([], f)
        except Exception:
            pass


def check_sentinel_status():
    """Check Sentinel health and return status message"""
    try:
        state_file = Path(__file__).parent / "sentinel_state.json"
        
        if not state_file.exists():
            return "⚠️ Sentinel state file missing"
        
        with open(state_file) as f:
            state = json.load(f)
        
        pid = state.get("pid")
        failures = state.get("failures", 0)
        restarts = state.get("restarts", 0)
        started = state.get("started", "unknown")[:10]
        
        # Check if process is alive
        try:
            import signal
            os.kill(pid, 0)
            status = "✅ Running"
        except:
            status = "❌ Dead"
        
        msg = f"""◼️ Sentinel Status

{status}
PID: {pid}
Started: {started}
Failures: {failures}
Restarts: {restarts}"""
        
        return msg
    
    except Exception as e:
        return f"⚠️ Error checking status: {e}"


def main():
    log("=== Telegram Alerts Starting ===")
    
    if not TOKEN or not CHAT_ID:
        log("WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        log("Set them as env vars or in config")
    
    last_sent = {"cost": "", "health": "", "custom": ""}
    
    while True:
        try:
            # Check for custom alerts
            alerts = read_alerts()

            if alerts:
                for alert in alerts:
                    alert_type = alert.get("type", "custom")
                    message = alert.get("message", "")
                    
                    # Avoid duplicate sends per type
                    if last_sent.get(alert_type) != message:
                        success, result = send_message(message)
                        if success:
                            log(f"Sent {alert_type} alert")
                            last_sent[alert_type] = message
                        else:
                            log(f"Failed to send {alert_type}: {result}")
                # Clear alerts once processed so they don't resend forever
                clear_alerts()
            
            # Periodic health report (every hour)
            # Only enabled if ALERT_HOURLY_STATUS=1 is set in env
            if os.environ.get("ALERT_HOURLY_STATUS") == "1":
                now = datetime.utcnow()
                if now.minute == 0:  # Every hour
                    status_msg = check_sentinel_status()
                    if last_sent.get("health") != status_msg:
                        send_message(status_msg)
                        last_sent["health"] = status_msg
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Stopped")
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(CHECK_INTERVAL)
    
    log("=== Telegram Alerts Exiting ===")


if __name__ == "__main__":
    main()
