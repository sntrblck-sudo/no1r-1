#!/usr/bin/env python3
"""task_loop.py

Very small autonomous task loop for no1r.

Current behavior (safe v1):
- Ensure tasks.json exists with a basic structure.
- If there is no PLANNED task, enqueue a simple "observe_markets" task.
- Take the first PLANNED task, mark it DOING → DONE, and log a brief note.

For now this does NOT hit external APIs; it's a scaffold to be expanded later.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
TASKS_FILE = WORKSPACE / "tasks.json"
TASK_LOG = WORKSPACE / "task_loop.log"


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with TASK_LOG.open("a") as f:
        f.write(f"[{ts}] {msg}\n")


def load_tasks() -> dict:
    if not TASKS_FILE.exists():
        return {"tasks": []}
    try:
        return json.loads(TASKS_FILE.read_text())
    except Exception:
        return {"tasks": []}


def save_tasks(data: dict) -> None:
    TASKS_FILE.write_text(json.dumps(data, indent=2))


def ensure_task_queue(data: dict) -> None:
    tasks = data.setdefault("tasks", [])
    has_planned = any(t.get("status") == "planned" for t in tasks)
    if not has_planned:
        now = datetime.now(timezone.utc).isoformat()
        task_id = f"{now}_observe-markets"
        tasks.append({
            "id": task_id,
            "kind": "observe_markets",
            "status": "planned",
            "created_at": now,
        })
        log(f"Enqueued task {task_id} (observe_markets)")


def run_one_task(data: dict) -> None:
    tasks = data.setdefault("tasks", [])
    task = next((t for t in tasks if t.get("status") == "planned"), None)
    if not task:
        log("No planned tasks to run.")
        return

    task_id = task["id"]
    kind = task.get("kind", "unknown")
    log(f"Starting task {task_id} kind={kind}")
    task["status"] = "doing"

    # v1: we only log; real behavior can be plugged in later.
    if kind == "observe_markets":
        # Placeholder: in future, this would scan a few safe sources.
        log("(observe_markets) Placeholder run: no external calls yet.")
    else:
        log(f"Unknown task kind={kind}, skipping behavior.")

    task["status"] = "done"
    task["completed_at"] = datetime.now(timezone.utc).isoformat()
    log(f"Completed task {task_id}")


def main() -> None:
    data = load_tasks()
    ensure_task_queue(data)
    run_one_task(data)
    save_tasks(data)


if __name__ == "__main__":
    main()
