#!/usr/bin/env bash
# backup_local.sh - simple local OpenClaw backup
#
# - Archives ~/.openclaw into ~/openclaw-backups/openclaw-YYYY-MM-DD_HHMM.tar.gz
# - Keeps the last 7 backups by date, deletes older ones
#
# This is a local script we fully own, independent of any skill wrapper.

set -euo pipefail

BACKUP_ROOT="$HOME/openclaw-backups"
SRC_DIR="$HOME/.openclaw"
TIMESTAMP="$(date +%Y-%m-%d_%H%M)"
DEST_FILE="$BACKUP_ROOT/openclaw-${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_ROOT"

if [ ! -d "$SRC_DIR" ]; then
  echo "[backup_local] Source dir $SRC_DIR does not exist" >&2
  exit 1
fi

# Create backup archive

echo "[backup_local] Creating backup: $DEST_FILE"
tar -czf "$DEST_FILE" -C "$HOME" .openclaw

echo "[backup_local] Backup created"

# Rotate to keep last 7 backups

echo "[backup_local] Rotating backups (keep last 7)"
cd "$BACKUP_ROOT"
ls -1t openclaw-*.tar.gz 2>/dev/null | sed -n '8,$p' | xargs -r rm -f

echo "[backup_local] Done"
