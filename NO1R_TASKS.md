# no1r Tasks (Registry Overview)

This file documents the actions exposed through `no1r.py`.

Usage:

```bash
cd ~/.openclaw/workspace
python3 no1r.py --task <name>
```

Each task is small, local, and designed to be safe and reversible.

---

## Tasks

### inclawbate-analytics

```bash
python3 no1r.py --task inclawbate-analytics
```

**What it does**

- Calls Inclawbate's public analytics endpoint (read-only).
- Writes a fresh `inclawbate_state.json` snapshot.
- Updates `inclawbate_summary.md` with a human-readable summary.
- Lightly nudges the `inclawbate` item in `attention_items.jsonl` (urgency + last_action_epoch).
- Runs `attention_tension.py` to recompute tension and reorder `attention_items.jsonl`.

**Why it exists**

To keep Inclawbate awareness up to date and aligned with the attention/tension model without touching funds.

---

### attention-tension

```bash
python3 no1r.py --task attention-tension
```

**What it does**

- Reads `attention_items.jsonl`.
- Computes a simple tension score per item:
  - `tension = base_priority * age_factor` (age derived from last_action_epoch).
- Rewrites `attention_items.jsonl` sorted by tension.
- Prints a brief summary including top items.

**Why it exists**

To turn a static list of topics/goals into a living priority queue that reflects both importance and neglect.

---

### ops-inbox

```bash
python3 no1r.py --task ops-inbox
```

**What it does**

- Probes local system state:
  - `openclaw status` (gateway/dashboard),
  - Sentinel `/health` + `sentinel.log` tail,
  - `openclaw cron list` (cron jobs and statuses),
  - `inclawbate_state.json` (Inclawbate staking/TVL snapshot, read-only).
- Ranks domains by tension and prints a compact "ops inbox" view:

  ```text
  OPS   [OK/WARN/FAIL] reason
  CRON  [OK/WARN/FAIL] reason
  DFI   [OBS/OK/...]   reason
  ```

- Prints brief raw details (status snippets, health, logs).
- Writes `ops_state.json` with coarse statuses for other tools.

**Why it exists**

To give a fast, tension-aware snapshot of what actually deserves attention in OPS/CRON/DFI, without reading full logs.

---

### patterns-mirror

```bash
python3 no1r.py --task patterns-mirror
```

**What it does**

- Reads:
  - `attention_items.jsonl`,
  - `ops_state.json` (if present),
  - `inclawbate_state.json` (if present).
- Writes `patterns.md` with short bullet points about:
  - top attention items,
  - low-bucket items,
  - last ops flags (gateway/sentinel/cron/inclawbate),
  - Inclawbate staking/price snapshot.

**Why it exists**

To pre-digest recurring patterns for no1r (and humans) so suggestions can be based on trends instead of only last-snapshot state.

---

### finance-sim

```bash
python3 no1r.py --task finance-sim
```

**What it does**

- Loads `finance_state.json` (or creates a default simulated state).
- Runs a single simulation tick:
  - if `balance_sim >= monthly_vps_cost`, subtracts the cost and notes that rent was covered,
  - otherwise, notes that rent could not be covered.
- Saves the updated simulated state back to `finance_state.json`.
- Prints a short summary of the simulated finance status.

**Why it exists**

To rehearse basic budgeting and survival logic (e.g., "can we cover VPS rent?") in a purely simulated environment with no real funds, accounts, or APIs.
