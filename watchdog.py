#!/usr/bin/env python3
"""
Watchdog - Monitors Sentinel and restarts if dead
With error protection and self-healing
"""

import os
import sys
import time
import subprocess
import signal
import json
from pathlib import Path

SENTINEL_PID_FILE = Path(__file__).parent / "sentinel_state.json"
SENTINEL_SCRIPT = Path(__file__).parent / "sentinel.py"
LOG_FILE = Path(__file__).parent / "watchdog.log"
CHECK_INTERVAL = 60  # 1 min
MAX_CONSECUTIVE_FAILURES = 10  # Give up after this many
MAX_MEMORY_MB = 500  # Restart if Sentinel uses > 500MB
MIN_DISK_SPACE_MB = 100  # Alert if < 100MB free

# Graceful shutdown
import signal
def signal_handler(signum, frame):
    log(f"Received {signum}, exiting...")
    sys.exit(0)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def log(msg):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
            f.flush()
    except:
        pass


def get_sentinel_memory():
    """Get Sentinel process memory in MB (Linux /proc)"""
    try:
        if not SENTINEL_PID_FILE.exists():
            return 0
        
        with open(SENTINEL_PID_FILE) as f:
            state = json.load(f)
        
        pid = state.get("pid")
        if not pid:
            return 0
        
        # Read from /proc/[pid]/status
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    # Format: "VmRSS:    12345 kB"
                    kb = int(line.split()[1])
                    return kb / 1024
        
        return 0
    
    except:
        return 0


def check_disk_space():
    """Check available disk space in MB"""
    try:
        stat = os.statvfs(os.getcwd())
        return (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
    except:
        return -1


def is_sentinel_alive():
    try:
        if not SENTINEL_PID_FILE.exists():
            return False
        
        with open(SENTINEL_PID_FILE) as f:
            state = json.load(f)
        
        pid = state.get("pid")
        if not pid:
            return False
        
        os.kill(pid, 0)
        return True
        
    except:
        return False


def start_sentinel():
    log("Starting Sentinel...")
    try:
        subprocess.Popen(
            ["python3", str(SENTINEL_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        time.sleep(3)
        
        if is_sentinel_alive():
            log("Sentinel started")
            return True
        return False
    except Exception as e:
        log(f"Start failed: {e}")
        return False


def main():
    log("=== Watchdog v3 Starting ===")
    sys.stdout.flush()
    
    consecutive_failures = 0
    
    while True:
        try:
            # Check disk space
            disk_free = check_disk_space()
            if disk_free > 0 and disk_free < MIN_DISK_SPACE_MB:
                log(f"WARNING: Low disk space ({disk_free:.0f}MB)")
            
            # Check memory
            mem_mb = get_sentinel_memory()
            if mem_mb > MAX_MEMORY_MB:
                log(f"WARNING: High memory usage ({mem_mb:.0f}MB), restarting...")
                try:
                    with open(SENTINEL_PID_FILE) as f:
                        state = json.load(f)
                    os.kill(state["pid"], 9)
                except:
                    pass
                time.sleep(2)
                start_sentinel()
                consecutive_failures += 1
            else:
                alive = is_sentinel_alive()
                
                if alive:
                    if consecutive_failures > 0:
                        log(f"Recovered ({consecutive_failures} fails)")
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    log(f"Dead (#{consecutive_failures})")
                    
                    if consecutive_failures >= 2:
                        if consecutive_failures > MAX_CONSECUTIVE_FAILURES:
                            log(f"ERROR: Max failures reached ({MAX_CONSECUTIVE_FAILURES}), giving up")
                            # Try one more time after a long wait
                            consecutive_failures = MAX_CONSECUTIVE_FAILURES - 1
                        else:
                            start_sentinel()
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Stopped")
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
