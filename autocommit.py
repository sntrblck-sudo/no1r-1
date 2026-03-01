#!/usr/bin/env python3
"""
Git Autocommit - Auto-commits workspace changes
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent
GITIGNORE = WORKSPACE / ".gitignore"
LOG_FILE = WORKSPACE / "autocommit.log"
CHECK_INTERVAL = int(os.environ.get("AUTOCOMMIT_INTERVAL", "600"))  # 10 min default


def log(msg):
    timestamp = datetime.utcnow().isoformat() + "Z"
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run(cmd, cwd=None):
    """Run shell command"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd or WORKSPACE,
            capture_output=True, text=True, timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_changed_files():
    """Get list of changed/untracked files"""
    code, out, _ = run("git status --porcelain")
    if code != 0:
        return []
    
    files = [line[3:].strip() for line in out.strip().split("\n") if line]
    return files


def commit_changes():
    """Commit any changes"""
    files = get_changed_files()
    
    if not files:
        return False, "No changes"
    
    # Add files
    for f in files:
        run(f"git add {f}")
    
    # Create commit message
    file_list = ", ".join(files[:5])
    if len(files) > 5:
        file_list += f" (+{len(files)-5} more)"
    
    msg = f"autonomy: Auto-commit {file_list}"
    
    # Commit
    code, _, err = run(f'git commit -m "{msg}"')
    
    if code == 0:
        return True, f"Committed: {file_list}"
    else:
        # No changes to commit is OK
        if "nothing to commit" in err.lower():
            return False, "No changes"
        return False, f"Error: {err}"


def main():
    log("=== Autocommit Starting ===")
    
    # Initialize git if needed
    code, _, _ = run("git rev-parse --git-dir")
    if code != 0:
        run("git init")
        log("Initialized git repo")
    
    # Always set config (in case init wasn't needed)
    run("git config user.email 'no1r@openclaw.local'")
    run("git config user.name 'no1r'")
    
    # Create .gitignore if missing
    if not GITIGNORE.exists():
        with open(GITIGNORE, "w") as f:
            f.write("""# Temp
*.log
*.log.*
*.pyc
__pycache__/

# State
*_state.json
.model-health-state.json

# OpenClaw
.openclaw/
node_modules/
""")
    
    commits_today = 0
    
    while True:
        try:
            changed = get_changed_files()
            
            if changed:
                success, msg = commit_changes()
                if success:
                    commits_today += 1
                    log(msg)
            
            # Daily reset
            now = datetime.utcnow()
            if now.hour == 0 and now.minute == 0:
                commits_today = 0
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Stopped")
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(CHECK_INTERVAL)
    
    log("=== Autocommit Exiting ===")


if __name__ == "__main__":
    main()
