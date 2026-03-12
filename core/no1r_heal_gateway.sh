#!/bin/bash
# Wrapper script for minimal heal action: restart/openclaw-gateway.service
# Intended to be run via sudo by dedicated user (no1r_heal)

LOG=/var/log/no1r_heal.log
DISABLE_FLAG=/etc/no1r/heal_disabled
RATEFILE=/var/run/no1r_heal_last

# Check disable flag
if [ -f "$DISABLE_FLAG" ]; then
  echo "$(date -u +%FT%TZ) - heal disabled via $DISABLE_FLAG" >> "$LOG"
  exit 2
fi

# Rate limit: no more than one restart per 300 seconds
if [ -f "$RATEFILE" ]; then
  last=$(cat "$RATEFILE")
  now=$(date +%s)
  diff=$((now - last))
  if [ "$diff" -lt 300 ]; then
    echo "$(date -u +%FT%TZ) - rate-limited: only $diff seconds since last heal" >> "$LOG"
    exit 3
  fi
fi

# Log intent
echo "$(date -u +%FT%TZ) - heal requested: restarting openclaw-gateway.service" >> "$LOG"

# Determine service owner and main PID (if openclaw-gateway process exists)
PID=$(pgrep -f openclaw-gateway | head -n1 || true)
SERVICE_USER=""
if [ -n "$PID" ] && [ -d "/proc/$PID" ]; then
  SERVICE_USER=$(stat -c '%U' /proc/$PID || true)
fi
if [ -z "$SERVICE_USER" ]; then
  SERVICE_USER="sntrblck"
fi

# 1) Try user-level systemd as the service owner (best-effort)
if sudo -u "$SERVICE_USER" systemctl --user restart openclaw-gateway.service 2>/dev/null; then
  sudo -u "$SERVICE_USER" systemctl --user status openclaw-gateway.service --no-pager >> "$LOG" 2>&1 || true
  echo "$(date -u +%FT%TZ) - heal success (user systemd as $SERVICE_USER)" >> "$LOG"
  date +%s > "$RATEFILE"
  exit 0
fi

# 2) Try system-level systemd as a fallback
if /bin/systemctl restart openclaw-gateway.service 2>/dev/null; then
  /bin/systemctl status openclaw-gateway.service --no-pager >> "$LOG" 2>&1 || true
  echo "$(date -u +%FT%TZ) - heal success (systemd)" >> "$LOG"
  date +%s > "$RATEFILE"
  exit 0
fi

# 3) Fallback: signal the running process (kill TERM) and rely on user systemd to restart it
if [ -n "$PID" ]; then
  echo "$(date -u +%FT%TZ) - fallback: sending TERM to PID $PID" >> "$LOG"
  kill -TERM "$PID" >> "$LOG" 2>&1 || true
  sleep 2
  # Check if a new PID is present
  NEWPID=$(pgrep -f openclaw-gateway | head -n1 || true)
  if [ -n "$NEWPID" ] && [ "$NEWPID" != "$PID" ]; then
    echo "$(date -u +%FT%TZ) - heal success (process restarted as PID $NEWPID)" >> "$LOG"
    date +%s > "$RATEFILE"
    exit 0
  else
    echo "$(date -u +%FT%TZ) - fallback heal failed (process did not restart)" >> "$LOG"
  fi
else
  echo "$(date -u +%FT%TZ) - no PID found for openclaw-gateway, cannot fallback to kill" >> "$LOG"
fi

# If we reach here, heal failed
echo "$(date -u +%FT%TZ) - heal failed" >> "$LOG"
sudo -u "$SERVICE_USER" systemctl --user status openclaw-gateway.service --no-pager >> "$LOG" 2>&1 || true
/bin/systemctl status openclaw-gateway.service --no-pager >> "$LOG" 2>&1 || true
exit 4
