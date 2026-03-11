#!/usr/bin/env bash
# ops.sh - small wrapper for common ops entrypoints

cd "$(dirname "$0")" || exit 1

case "$1" in
  status|"")
    # Default: ops snapshot
    python3 ops_inbox.py
    ;;
  wallet)
    if [ -z "$BASESCAN_API_KEY" ]; then
      echo "BASESCAN_API_KEY not set; export it before running wallet snapshot." >&2
      exit 1
    fi
    python3 base_wallet_snapshot.py
    ;;
  judge-seed)
    python3 judgement_log.py
    ;;
  *)
    echo "Usage: ./ops.sh [status|wallet|judge-seed]" >&2
    exit 1
    ;;
esac
