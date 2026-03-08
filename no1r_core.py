#!/usr/bin/env python3
"""no1r_core.py

Shared helpers for no1r scripts:
- paths
- JSON/JSONL helpers
- time helpers
- simple logging

This is intentionally small and boring; scripts can import from here instead
of rolling their own utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json
import sys
import time
from datetime import datetime, timezone

# Workspace root
WORKSPACE = Path("/home/sntrblck/.openclaw/workspace").resolve()


# ---------- time helpers ----------

UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(UTC)


def to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(UTC).isoformat()


def to_epoch(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    return int(dt.astimezone(UTC).timestamp())


def epoch_now() -> int:
    return int(time.time())


# ---------- JSON helpers ----------


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def write_jsonl(path: Path, items: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ---------- logging ----------


def log(msg: str, scope: str = "core") -> None:
    ts = to_iso(now_utc()) or ""
    sys.stdout.write(f"[{ts}][{scope}] {msg}\n")
    sys.stdout.flush()
