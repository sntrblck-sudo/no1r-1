#!/bin/bash
# Diagnostic script to verify no1r heal installation. Run as root or with sudo.
set -euo pipefail

echo "--- wrapper file and perms ---"
ls -l /usr/local/bin/no1r_heal_gateway.sh || echo "MISSING: /usr/local/bin/no1r_heal_gateway.sh"

echo "\n--- visudo syntax check ---"
visudo -c || echo "visudo reported issues"

echo "\n--- sudoers file (no1r_heal) ---"
if [ -f /etc/sudoers.d/no1r_heal ]; then
  cat /etc/sudoers.d/no1r_heal
else
  echo "MISSING: /etc/sudoers.d/no1r_heal"
fi

echo "\n--- allowed commands for no1r_heal ---"
sudo -l -U no1r_heal || true

echo "\n--- recent heal log (last 200 lines) ---"
if [ -f /var/log/no1r_heal.log ]; then
  tail -n 200 /var/log/no1r_heal.log
else
  echo "MISSING: /var/log/no1r_heal.log"
fi

echo "\n--- systemd status: openclaw-gateway.service ---"
systemctl status openclaw-gateway.service --no-pager || echo "Service not found or inactive"

echo "\n--- diagnostic complete ---"
