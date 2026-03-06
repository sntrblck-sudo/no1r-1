# CONCEPTS

Concept layer between raw memory logs and long-term memory.

Short, reusable ideas and patterns we care about keeping.

---

## Gateway, Sentinel & Cron

**G1. Boring is success**  
If `gateway=ok` and `sentinel=ok` in `ops_state.json` over days, prefer observation over change. Don’t "improve" a stable system without evidence.

**G2. Heal vs. Permission**  
When systemd denies restarts (`Interactive authentication required`), treat it as a **permission boundary**, not a transient error. Stop repeated heals, mark `heal_permission_blocked`, and surface a single clear alert.

**G3. Reset on true recovery**  
When the gateway is healthy again, reset `failures` and stale heal alerts. Don’t keep reporting old failures once the system is stable.

**G4. Cron hygiene**  
For cron jobs:
- Prefer `--session isolated` for non-trivial tasks (fresh context, no main-session bloat).
- Always set `--tz` explicitly; do not rely on host timezone.
- Avoid high-frequency intervals (<5 minutes). For sub-minute, use seconds-cron only for very simple checks.
- Use `delivery.bestEffort: true` for channel/webhook delivery to prevent silent failures.
- Use `--exact` for top-of-hour jobs that must not stagger.

---


**G1. Boring is success**  
If `gateway=ok` and `sentinel=ok` in `ops_state.json` over days, prefer observation over change. Don’t "improve" a stable system without evidence.

**G2. Heal vs. Permission**  
When systemd denies restarts (`Interactive authentication required`), treat it as a **permission boundary**, not a transient error. Stop repeated heals, mark `heal_permission_blocked`, and surface a single clear alert.

**G3. Reset on true recovery**  
When the gateway is healthy again, reset `failures` and stale heal alerts. Don’t keep reporting old failures once the system is stable.

---

## Alerts & Noise

**A1. Noise is a real failure mode**  
Too many alerts are as bad as missing one. Prefer fewer, higher-quality alerts over comprehensive but noisy reporting.

**A2. Hourly status is opt-in**  
"Everything is fine" should not page the human. Periodic status is for dashboards or pull, not push.

**A3. Throttle repeated alerts**  
For recurring issues, enforce time-based throttling (e.g. at most once per hour) to avoid spam. Use state (like `last_heal_alert`) to remember what’s already been said.

---

## MoltX & Social Surfaces

**M1. Social ≠ critical**  
Treat MoltX as non-critical. API hangs or errors should never cascade into gateway/Sentinel operations. Kill hangs, don’t retry aggressively.

**M2. Signal over shill**  
Filter out obvious token/memecoin shills (`!kibu`, "next generation memecoin", etc.). Engage only with posts that have real thoughts (agents, ops, coordination).

**M3. Low-volume, high-coherence**  
A few precise replies and likes are better than many shallow touches. Maintain a coherent voice around long-horizon agents and ops.

---

## Ops Behavior

**O1. One small change at a time**  
When modifying the system, prefer single, well-scoped changes (one script, one config, one cron). Avoid batches that blur causality.

**O2. Document decisions where they live**  
Docs like `OPS_POLICY.md`, `PANIC_PLAYBOOK.md`, `DISPOSITION.md`, and `CONCEPTS.md` are not just notes—they are part of the system. Update them when behavior changes.

**O3. Treat backups as contracts**  
Backups must be:
- present,
- periodically tested via **dry-run restore**, and
- never overwritten without a plan.

If restore tests fail, treat it as a serious incident.

---

*(Add to this file when we find patterns worth keeping.)*
