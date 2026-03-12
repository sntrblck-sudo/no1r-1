#!/bin/bash
# Simple monitor: count heal requests in the last 30 minutes and alert if above threshold
LOG=/var/log/no1r_heal.log
THRESHOLD=3
WINDOW_MIN=30

if [ ! -f "$LOG" ]; then
  echo "no1r_heal log missing: $LOG"
  exit 0
fi

COUNT=$(awk -v d="$(date -d"-${WINDOW_MIN} minutes" +%Y-%m-%dT%H:%M)" '$0 > d && /heal requested/ {c++} END{print c+0}' "$LOG")

if [ "$COUNT" -ge "$THRESHOLD" ]; then
  echo "ALERT: $COUNT heal requests in last $WINDOW_MIN minutes (threshold $THRESHOLD)"
  # Append a pending alert for operator review
  jq -n --arg ts "$(date -u +%FT%TZ)" --arg msg "Heal attempts high: $COUNT in last ${WINDOW_MIN}m" '{type: "health", timestamp: $ts, message: $msg}' >> .pending_alerts.json
else
  echo "OK: $COUNT heal requests in last $WINDOW_MIN minutes"
fi
