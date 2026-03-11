#!/usr/bin/env python3
"""social_memory.py

Minimal social memory scaffold for Telegram users.

- Stores per-user profiles in social/users.jsonl
- Stores topic associations in social/topics.jsonl
- Provides helper functions to load/update profiles and topics.

This is a local-only system; data never leaves this machine.
"""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
SOCIAL_DIR = WORKSPACE / "social"
USERS_FILE = SOCIAL_DIR / "users.jsonl"
TOPICS_FILE = SOCIAL_DIR / "topics.jsonl"

SOCIAL_DIR.mkdir(exist_ok=True)


@dataclass
class InteractionStyle:
    tone: str = "neutral"  # neutral | casual | formal
    prefers_options: bool = True
    depth: str = "medium"  # shallow | medium | deep


@dataclass
class UserProfile:
    user_id: str
    username: Optional[str] = None
    first_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    topics_of_interest: List[str] = field(default_factory=list)
    interaction_style: InteractionStyle = field(default_factory=InteractionStyle)
    notes: List[str] = field(default_factory=list)

    def touch(self) -> None:
        self.last_seen = datetime.now(timezone.utc).isoformat()

    def add_topic(self, topic: str) -> None:
        if topic not in self.topics_of_interest:
            self.topics_of_interest.append(topic)

    def add_note(self, note: str) -> None:
        if note and note not in self.notes:
            self.notes.append(note)


@dataclass
class TopicRecord:
    topic: str
    users: List[str] = field(default_factory=list)
    last_discussed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def touch(self, user_id: str) -> None:
        if user_id not in self.users:
            self.users.append(user_id)
        self.last_discussed = datetime.now(timezone.utc).isoformat()


def _load_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    data = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except Exception:
                continue
    return data


def _save_jsonl(path: Path, records: List[dict]) -> None:
    with path.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def load_users() -> Dict[str, UserProfile]:
    raw = _load_jsonl(USERS_FILE)
    users: Dict[str, UserProfile] = {}
    for r in raw:
        style_raw = r.get("interaction_style", {})
        style = InteractionStyle(**style_raw)
        users[r["user_id"]] = UserProfile(
            user_id=r["user_id"],
            username=r.get("username"),
            first_seen=r.get("first_seen", datetime.now(timezone.utc).isoformat()),
            last_seen=r.get("last_seen", datetime.now(timezone.utc).isoformat()),
            topics_of_interest=r.get("topics_of_interest", []),
            interaction_style=style,
            notes=r.get("notes", []),
        )
    return users


def save_users(users: Dict[str, UserProfile]) -> None:
    records = []
    for u in users.values():
        rec = asdict(u)
        # interaction_style is a nested dataclass; ensure it is a plain dict
        rec["interaction_style"] = asdict(u.interaction_style)
        records.append(rec)
    _save_jsonl(USERS_FILE, records)


def load_topics() -> Dict[str, TopicRecord]:
    raw = _load_jsonl(TOPICS_FILE)
    topics: Dict[str, TopicRecord] = {}
    for r in raw:
        topics[r["topic"]] = TopicRecord(
            topic=r["topic"],
            users=r.get("users", []),
            last_discussed=r.get("last_discussed", datetime.now(timezone.utc).isoformat()),
        )
    return topics


def save_topics(topics: Dict[str, TopicRecord]) -> None:
    records = []
    for t in topics.values():
        records.append(asdict(t))
    _save_jsonl(TOPICS_FILE, records)


def touch_user(user_id: str, username: Optional[str] = None) -> UserProfile:
    users = load_users()
    profile = users.get(user_id)
    if not profile:
        profile = UserProfile(user_id=user_id, username=username)
        users[user_id] = profile
    else:
        if username and profile.username != username:
            profile.username = username
        profile.touch()
    save_users(users)
    return profile


def record_topic(user_id: str, topic: str) -> None:
    users = load_users()
    topics = load_topics()

    profile = users.get(user_id)
    if not profile:
        profile = UserProfile(user_id=user_id)
        users[user_id] = profile
    profile.add_topic(topic)
    profile.touch()

    tr = topics.get(topic)
    if not tr:
        tr = TopicRecord(topic=topic)
        topics[topic] = tr
    tr.touch(user_id)

    save_users(users)
    save_topics(topics)


if __name__ == "__main__":
    # Simple smoke test: touch a fake user and topic
    u = touch_user("telegram:test", "test_user")
    record_topic("telegram:test", "agent_income")
    print("Wrote/updated social memory for telegram:test")
