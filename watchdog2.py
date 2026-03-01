#!/usr/bin/env python3
"""
Watchdog for Watchdog - Monitors the watchdog process
"""

import os
import sys
import time
from pathlib import Path

WATCHDOG_SCRIPT = Path(__file__).parent / "watchdog.py"
LOG_FILE = Path(__file__).parent / "watchdog2.log"
CHECK_INTERVAL = 90  # Check every 90s


def log(msg):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def is_watchdog_alive():
    """Check if watchdog is running"""
    try:
        # Look for watchdog process
        for line in os.popen("pgrep -f 'python3.*watchdog.py'"):
            pid = int(line.strip())
            if pid != os.getpid():
                return True, pid
        return False, None
    except:
        return False, None


def start_watchdog():
    """Start the watchdog script"""
    try:
        os.popen(f"nohup python3 {WATCHDOG_SCRIPT} >> watchdog.log 2>&1 &")
        time.sleep(3)
        alive, pid = is_watchdog_alive()
        if alive:
            log(f"Watchdog started (PID {pid})")
            return True
        return False
    except Exception as e:
        log(f"Failed to start: {e}")
        return False


def main():
    log("=== Watchdog2 (for Watchdog) Starting ===")
    
    consecutive_failures = 0
    
    while True:
        try:
            alive, pid = is_watchdog_alive()
            
            if alive:
                if consecutive_failures > 0:
                    log(f"Watchdog recovered after {consecutive_failures} failures")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                log(f"Watchdog dead (#{consecutive_failures})")
                
                if consecutive_failures >= 2:
                    log("Restarting watchdog...")
                    start_watchdog()
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Stopped")
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
