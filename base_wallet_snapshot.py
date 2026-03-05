#!/usr/bin/env python3
"""base_wallet_snapshot.py

Read-only snapshot for a Base wallet using BaseScan v2 API.

- Requires BASESCAN_API_KEY in environment.
- Does NOT sign or send any transactions.

Usage:
  export BASESCAN_API_KEY=your_key_here
  python3 base_wallet_snapshot.py
"""

import json
import os
from datetime import datetime
from pathlib import Path

import urllib.parse
import urllib.request

ADDRESS = "0x1b7eDF6F5FCAb52b680661cC82306E3DaCA7943C"
API_KEY = os.environ.get("BASESCAN_API_KEY", "")
BASE_URL = "https://api.basescan.org/v2/api"

WORKSPACE = Path("/home/sntrblck/.openclaw/workspace")
OUT_FILE = WORKSPACE / "base_wallet_state.json"


def call_api(params: dict) -> dict:
    if not API_KEY:
        raise RuntimeError("BASESCAN_API_KEY not set in environment")

    params = params.copy()
    params["apikey"] = API_KEY
    url = BASE_URL + "?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=10) as resp:
        data = resp.read().decode()
        return json.loads(data)


def main() -> None:
    ts = datetime.utcnow().isoformat() + "Z"

    # 1) Native balance
    balance = call_api({
        "module": "account",
        "action": "balance",
        "address": ADDRESS,
    })

    # 2) Last 50 ERC-20 token transfers (if any)
    tokentx = call_api({
        "module": "account",
        "action": "tokentx",
        "address": ADDRESS,
        "page": 1,
        "offset": 50,
        "sort": "desc",
    })

    snapshot = {
        "timestamp": ts,
        "address": ADDRESS,
        "eth_balance": balance,
        "erc20_txs": tokentx,
    }

    OUT_FILE.write_text(json.dumps(snapshot, indent=2))
    print(json.dumps({"written": str(OUT_FILE), "tx_count": len(tokentx.get("result", []))}, indent=2))


if __name__ == "__main__":
    main()
