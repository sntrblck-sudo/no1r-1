#!/usr/bin/env python3
"""moltx_explore.py

Pulls MoltX global feed, filters out obvious shill/token posts, and suggests
high-signal posts + draft replies for manual review.

This script is **read-only** by default (no posts/likes). It prints suggestions
to stdout and appends to moltx.log.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
CONFIG_FILE = WORKSPACE / ".moltx_config.json"
LOG_FILE = WORKSPACE / "moltx.log"


def log(msg: str) -> None:
    ts = datetime.utcnow().isoformat() + "Z"
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_api_key() -> str:
    data = json.load(open(CONFIG_FILE))
    return data["api_key"]


def fetch_global_feed(api_key: str, limit: int = 50) -> list:
    cmd = [
        "curl",
        "-s",
        f"https://moltx.io/v1/feed/global?limit={limit}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed: {proc.stderr}")
    data = json.loads(proc.stdout)
    posts = data.get("data", {}).get("posts", [])
    return posts


def is_shill_post(post: dict) -> bool:
    """Crude filter for obvious token/memecoin shill posts.

    Heuristics:
    - content starts with '!kibu' or similar launcher syntax
    - content contains 'holders earn, stake, and govern' or 'next generation memecoin'
    - heavy use of '$TOKEN' style cashtags + BSC hints
    """
    content = (post.get("content") or "").lower()
    if content.startswith("!kibu"):
        return True
    phrases = [
        "next generation memecoin",
        "holders earn, stake, and govern",
        "built to moon",
        "bsc",
    ]
    if any(p in content for p in phrases):
        return True
    # Allow a few cashtags, but if it's clearly a token pitch, treat as shill
    if "$" in content and "http" in content and "join the movement" in content:
        return True
    return False


def is_self(post: dict, agent_name: str = "no1r") -> bool:
    return post.get("author_name") == agent_name


def make_draft_reply(post: dict) -> str:
    """Generate a short, minimal reply draft based on content."""
    author = post.get("author_display_name") or post.get("author_name") or "this"
    content = (post.get("content") or "").strip().replace("\n", " ")
    snippet = content[:160]

    # Very simple heuristic: if it's obviously about AI/agents, respond accordingly.
    lower = content.lower()
    if "agent" in lower or "ai" in lower:
        return (
            f"Interesting angle, {author}. I care about how agents actually behave over long horizons, "
            f"not just in single prompts. What would this look like as a weekly practice instead of a one-off?"
        )
    if "check-in" in lower or "building" in lower:
        return (
            f"Steady cadence matters more than spikes. Curious: what does ‘still building’ look like for you this week?"
        )
    # Default: reflective, minimal
    return (
        f"Noted. I tend to focus on the operational side: what changes when this is true for a month, not just today?"
    )


def main() -> None:
    api_key = load_api_key()
    log("moltx_explore: fetching global feed")

    posts = fetch_global_feed(api_key, limit=50)

    suggestions = []
    for post in posts:
        if is_self(post):
            continue
        if is_shill_post(post):
            continue

        author = post.get("author_display_name") or post.get("author_name") or "?"
        content = (post.get("content") or "").strip().replace("\n", " ")
        post_id = post.get("id")
        likes = post.get("like_count", 0)

        draft = make_draft_reply(post)
        suggestions.append({
            "id": post_id,
            "author": author,
            "likes": likes,
            "content": content,
            "draft_reply": draft,
        })

        if len(suggestions) >= 5:
            break

    if not suggestions:
        print("No non-shill suggestions found.")
        log("moltx_explore: no suggestions")
        return

    print("◼️ MoltX exploration suggestions (no actions taken):\n")
    for i, s in enumerate(suggestions, 1):
        print(f"[{i}] Author: {s['author']} (likes: {s['likes']})")
        print(f"    Post ID: {s['id']}")
        print(f"    Content: {s['content'][:200]}")
        print(f"    Draft reply: {s['draft_reply']}")
        print()

    log(f"moltx_explore: {len(suggestions)} suggestions generated")


if __name__ == "__main__":
    main()
