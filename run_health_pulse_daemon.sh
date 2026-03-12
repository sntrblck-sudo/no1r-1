#!/usr/bin/env bash
# Lightweight health pulse daemon (runs in background). Not a systemd unit; survives until process killed.
WORKDIR="/home/sntrblck/.openclaw/workspace"
cd "$WORKDIR" || exit 1
PIDFILE="$WORKDIR/health_pulse.pid"
LOG="$WORKDIR/health_pulse.daemon.log"

# If already running, exit
if [ -f "$PIDFILE" ]; then
  pid=$(cat "$PIDFILE")
  if kill -0 "$pid" 2>/dev/null; then
    echo "health_pulse daemon already running (pid=$pid)" >> "$LOG"
    exit 0
  else
    rm -f "$PIDFILE"
  fi
fi

# Run loop
(while true; do
  sleep $((RANDOM % 300))
  /usr/bin/python3 "$WORKDIR/health_pulse.py" >> "$LOG" 2>&1
  # sleep until next 15-minute boundary roughly
  sleep 900
done) &

echo $! > "$PIDFILE"

echo "started health_pulse daemon pid=$(cat $PIDFILE)" >> "$LOG"
