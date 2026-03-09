# Visual Identity Notes (Ops / DeFi View)

Lightweight conventions for how no1r presents system state in text.

## Status Legend

- **Status codes**
  - `OK`   → healthy, no immediate attention needed
  - `WARN` → something is off; worth a look soon
  - `FAIL` → broken or repeatedly failing; needs attention
  - `OBS`  → observe / watch; interesting but not urgent

- **Domains**
  - `OPS` → Gateway + Sentinel / core runtime
  - `CRON` → OpenClaw cron / automation
  - `DFI` → DeFi / Inclawbate state (read-only)
  - `SOC` → Social / MoltX presence (low-volume)

## Default Ops Brief Format

no1r presents ops/DeFi status in this compact structure:

```text
OPS   [OK]   short reason
CRON  [WARN] short reason
DFI   [OBS]  short reason
SOC   [OK]   short reason (if relevant)
```

Followed by, when requested:

```text
Details:
- Gateway: ...
- Sentinel /health: ...
- Cron: ...
- Inclawbate: ...
```

## Example Snapshot

```text
◼️ ops_inbox snapshot @ 2026-03-08T15:28:42Z

OPS   [OK]   gateway+sentinel healthy, low latency
CRON  [WARN] daily-backup + no1r-task-loop error in cron list
DFI   [OBS]  Inclawbate TVL=0, stakers=0, ~1060 humans, 994 wallets

Details:
- Gateway status snippet: ...
- Sentinel /health: ...
- Sentinel log tail: ...
- Cron list snippet: ...
```

## Usage

- This legend/format should be used for:
  - proactive daily digests (when warranted),
  - on-demand status / ops / Inclawbate requests.
- The goal is to minimize text walls and give a fast visual grasp of state.
