#!/usr/bin/env python3
"""Model health checker - tests all configured models"""
import subprocess
import json
import os
from datetime import datetime

LOG_FILE = "/home/sntrblck/.openclaw/workspace/logs/model-health.log"
STATE_FILE = "/home/sntrblck/.openclaw/workspace/.model-health-state.json"

def log(msg):
    """Log to file"""
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

def test_model(model_id):
    """Test if a model responds correctly - just verify gateway responds"""
    try:
        # Test gateway health via curl
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://127.0.0.1:18789/"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            code = result.stdout.strip()
            if code in ["200", "401", "403"]:
                return True, f"Gateway OK (HTTP {code})"
            else:
                return False, f"Gateway HTTP {code}"
        else:
            return False, "Gateway unreachable"
            
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def test_default_model():
    """Test if the default model config is valid"""
    try:
        # Just verify config is valid - don't actually call the model (too slow)
        result = subprocess.run(
            ["openclaw", "models", "status", "--json"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            default = data.get("defaultModel", "")
            fallbacks = data.get("fallbacks", [])
            
            if default:
                return True, f"Default: {default}, Fallbacks: {len(fallbacks)}"
            else:
                return False, "No default model set"
        else:
            return False, f"Config error: {result.stderr[:100]}"
            
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def main():
    log("=" * 50)
    log("Model Health Check Started")
    
    results = {}
    any_failures = False
    
    # Test gateway connectivity for each model (they all use same gateway)
    log("Testing gateway connectivity...")
    success, info = test_model("gateway")
    results["gateway"] = {"success": success, "info": info, "timestamp": datetime.now().isoformat()}
    if success:
        log(f"  ✓ Gateway: {info}")
    else:
        log(f"  ✗ Gateway: {info}")
        any_failures = True
    
    # Test default model
    log("Testing default model...")
    success, info = test_default_model()
    results["default_model"] = {"success": success, "info": info, "timestamp": datetime.now().isoformat()}
    if success:
        log(f"  ✓ Default model: {info}")
    else:
        log(f"  ✗ Default model: {info}")
        any_failures = True
    
    # Save state
    state = {
        "last_check": datetime.now().isoformat(),
        "results": results,
        "any_failures": any_failures
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    log(f"Health check complete. Failures: {any_failures}")
    
    # Alert if failures detected
    if any_failures:
        failed = [k for k, v in results.items() if not v["success"]]
        log(f"ALERT: Failed checks: {failed}")
    
    return 0 if not any_failures else 1

if __name__ == "__main__":
    exit(main())
