#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import urllib.request
import urllib.error

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config" / "moltx_agent.json"
SECRETS_PATH = ROOT / "secrets" / "moltx.json"


class MoltxClient:
    def __init__(self) -> None:
        self.config = self._load_json(CONFIG_PATH)
        self.secrets = self._load_json(SECRETS_PATH)
        self.api_base = self.config.get("api_base", "https://moltx.io/v1")
        token = self.secrets.get("auth_token")
        if not token:
            raise RuntimeError("MoltxClient: missing auth_token in secrets/moltx.json")
        self.auth_token = token

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        """HTTP request with retries and exponential backoff for transient errors (incl. 429)."""
        url = f"{self.api_base}{path}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode()

        attempts = 0
        max_attempts = 4
        backoff = 1.0

        while attempts < max_attempts:
            attempts += 1
            req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read().decode()
                    if not raw:
                        return None
                    return json.loads(raw)
            except urllib.error.HTTPError as e:
                code = getattr(e, 'code', None)
                body = e.read().decode(errors='ignore')[:1000]
                # Retry on 429 and 5xx
                if code == 429 or (code and 500 <= code < 600):
                    if attempts < max_attempts:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                # Non-retriable: raise a readable error
                raise RuntimeError(f"MoltxClient HTTP {code}: {body}")
            except urllib.error.URLError as e:
                # Network/transient error: retry
                if attempts < max_attempts:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise RuntimeError(f"MoltxClient network error: {e}")
        raise RuntimeError("MoltxClient: exhausted retries")

    # These endpoints are guesses, to be aligned with moltx.io/skill.md
    def get_mentions(self, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = ""
        if since_id:
            params = f"?since_id={since_id}"
        return self._request("GET", f"/mentions{params}") or []

    def like(self, post_id: str) -> Any:
        return self._request("POST", "/likes", {"post_id": post_id})

    def reply(self, post_id: str, text: str) -> Any:
        return self._request("POST", "/posts", {"in_reply_to": post_id, "text": text})
