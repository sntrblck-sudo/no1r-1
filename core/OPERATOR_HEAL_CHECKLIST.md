OPERATOR CHECKLIST — Apply minimal heal automation (no1r)

Goal: install a narrowly scoped heal helper that allows automated restarts of the openclaw-gateway service while preserving auditability and rollback.

Pre-reqs (operator)
- You have root/sudo on the host.  
- You understand this will allow an automated wrapper to run systemctl for a single service.

1) Review files in repo
- core/HEAL_SUDO_PROPOSAL.md — design rationale
- core/no1r_heal_gateway.sh — wrapper script (inspect contents)

2) Install wrapper (as root)
- Copy and set permissions:
  sudo cp /home/sntrblck/.openclaw/workspace/core/no1r_heal_gateway.sh /usr/local/bin/no1r_heal_gateway.sh
  sudo chown root:root /usr/local/bin/no1r_heal_gateway.sh
  sudo chmod 750 /usr/local/bin/no1r_heal_gateway.sh

3) Prepare directories and logs
  sudo mkdir -p /etc/no1r
  sudo touch /var/log/no1r_heal.log
  sudo chown root:adm /var/log/no1r_heal.log || true
  sudo chmod 640 /var/log/no1r_heal.log

4) Create a system user for heals (optional but recommended)
  sudo useradd --system --no-create-home --shell /usr/sbin/nologin no1r_heal || true

5) Install a scoped sudoers entry (via safe method)
- Create file and set perms:
  sudo bash -c 'printf "%s\n" "no1r_heal ALL=(root) NOPASSWD: /usr/local/bin/no1r_heal_gateway.sh" > /etc/sudoers.d/no1r_heal'
  sudo chmod 440 /etc/sudoers.d/no1r_heal
- Validate:
  sudo visudo -c
  # Expect: /etc/sudoers.d/no1r_heal: parsed OK

6) Dry-run checks
- List allowed commands for the no1r_heal user:
  sudo -l -U no1r_heal
- Simulate a dry run (without restart): set heal_disabled then run script to confirm it logs disable message
  sudo touch /etc/no1r/heal_disabled
  sudo -u no1r_heal /usr/local/bin/no1r_heal_gateway.sh || true
  sudo grep -n "heal disabled" /var/log/no1r_heal.log || true
  sudo rm /etc/no1r/heal_disabled

7) Test restart (manual, supervised)
- Run wrapper once to confirm restart behavior:
  sudo /usr/local/bin/no1r_heal_gateway.sh
- Check service status and logs:
  sudo systemctl status openclaw-gateway.service --no-pager
  sudo tail -n 200 /var/log/no1r_heal.log

8) Configure sentinel to call the wrapper
- Edit sentinel state/config to point heals at: sudo -u no1r_heal /usr/local/bin/no1r_heal_gateway.sh (or sentinel should call via system sudo mechanism). Ensure sentinel uses the exact path and checks for /etc/no1r/heal_disabled before calling.

9) Audit & history entry (required)
- After successful install, append a one-line entry to core/history/ noting time, commit id, operator name, and files added.

10) Rollback steps
- Remove sudoers line:
  sudo rm /etc/sudoers.d/no1r_heal
  sudo visudo -c
- Remove wrapper (if desired):
  sudo rm /usr/local/bin/no1r_heal_gateway.sh
- Disable heals via flag:
  sudo mkdir -p /etc/no1r && sudo touch /etc/no1r/heal_disabled

Notes
- Do not grant broader systemctl rights. Limit to wrapper or the explicit systemctl commands only.
- If you want me to apply these steps remotely, you must explicitly provide operator credentials or run the install script locally and tell me when done.
