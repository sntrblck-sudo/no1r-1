#!/bin/bash
# Reset daily spend field in finance_state.json (simulation)
STATE=/home/sntrblck/.openclaw/workspace/finance_state.json
if [ ! -f "$STATE" ]; then
  echo "{}" > "$STATE"
fi
jq '.daily_spent = 0' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
echo "Reset daily_spent to 0 in $STATE"
