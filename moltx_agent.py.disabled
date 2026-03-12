#!/usr/bin/env python3
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from moltx_client import MoltxClient, CONFIG_PATH

ROOT = Path(__file__).parent


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path) as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def log(msg: str) -> None:
    cfg = load_json(CONFIG_PATH, {})
    log_file = ROOT / cfg.get("log_file", "moltx_agent.log")
    ts = datetime.utcnow().isoformat() + "Z"
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(log_file, "a") as f:
        f.write(line + "\n")


def run_once() -> None:
    cfg = load_json(CONFIG_PATH, {})
    state_path = ROOT / cfg.get("state_file", "moltx_state.json")
    drafts_path = ROOT / cfg.get("drafts_file", "moltx_drafts.json")

    state = load_json(state_path, {"last_seen_id": None, "daily_actions": 0, "daily_replies": 0, "last_reset": None})

    # Daily reset
    today = datetime.utcnow().date().isoformat()
    if state.get("last_reset") != today:
        state["daily_actions"] = 0
        state["daily_replies"] = 0
        state["last_reset"] = today

    max_actions = int(cfg.get("max_daily_actions", 20))
    max_replies = int(cfg.get("max_daily_replies", 5))

    if state["daily_actions"] >= max_actions:
        log("Daily MoltX action limit reached; skipping run")
        save_json(state_path, state)
        return

    client = MoltxClient()

    mentions = client.get_mentions(state.get("last_seen_id"))
    if not mentions:
        log("No new MoltX mentions")
        save_json(state_path, state)
        return

    drafts = load_json(drafts_path, [])

    templates = cfg.get("reply_templates", [])
    forbidden = [w.lower() for w in cfg.get("forbidden_keywords", [])]

    for m in mentions:
        post_id = m.get("id")
        text = (m.get("text") or "").lower()

        # Update last_seen_id monotonically
        state["last_seen_id"] = post_id or state.get("last_seen_id")

        if any(w in text for w in forbidden):
            log(f"Skipping mention {post_id} due to forbidden keyword")
            continue

        if state["daily_actions"] >= max_actions:
            break

        # Safe auto-like
        if cfg.get("safe_auto_like", True):
            try:
                client.like(post_id)
                state["daily_actions"] += 1
                log(f"Auto-liked mention {post_id}")
            except Exception as e:
                log(f"Failed to like {post_id}: {e}")

        # Controlled auto-reply with templates only
        if cfg.get("safe_auto_reply", True) and state["daily_replies"] < max_replies and templates:
            template = templates[state["daily_replies"] % len(templates)]
            try:
                client.reply(post_id, template)
                state["daily_actions"] += 1
                state["daily_replies"] += 1
                log(f"Auto-replied to {post_id} with template")
                continue
            except Exception as e:
                log(f"Failed to auto-reply to {post_id}: {e}")

        # Otherwise, create a draft entry
        drafts.append({
            "id": post_id,
            "text": m.get("text"),
            "created_at": m.get("created_at"),
            "draft": None,
            "reason": "needs_manual_review"
        })

    save_json(state_path, state)
    save_json(drafts_path, drafts)


if __name__ == "__main__":
    run_once()
