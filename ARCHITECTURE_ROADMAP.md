# PROJECT NO1R: ARCHITECTURAL ROADMAP (MARCH 2026)

## 1. Core Philosophy & Governance

- **Operational Mandate:** Boringly reliable personal operations.
- **Trust Model:** Read-only / No-custody for all financial and social integrations (Inclawbate, DeFi, MoltX).
- **Execution Layer:** Governance is enforced at the script level (OpenClaw skills and local code), not only in LLM prompts.
- **Version Control:** All state changes and code iterations are tracked via Git whenever possible.

---

## 2. Technical Stack

- **Environment:** Local Linux machine running OpenClaw.
- **Language:** Python 3.x for agents/scripts.
- **Storage:**
  - **Current:** Git-tracked JSON (e.g. `working_context.json`, `attention_items.jsonl`) and Markdown (`MEMORY.md`, daily `memory/YYYY-MM-DD.md`).
  - **Future:** ACID-compliant SQLite-based state engine for multi-instance support.
- **Memory Structure:**
  - Daily journals: `memory/YYYY-MM-DD.md`.
  - Long-term: `MEMORY.md`.
  - Structured logs: `style_memory.jsonl`, `judgements.jsonl`.

---

## 3. State Engine Blueprint (Future)

To enable multi-instance support (e.g., VPS workers), the system is moving toward a relational state model:

| Table            | Constraint           | Purpose                                                      |
|------------------|----------------------|--------------------------------------------------------------|
| `working_context`| `CHECK (id = 1)`     | Single source of truth for current objective/context.       |
| `attention_queue`| Tension-sorted view  | Prioritizes tasks based on decay and importance.            |
| `state_vars`     | key-value primary key| Stores high-frequency system flags and status codes.        |
| `audit_log`      | append-only          | Records writes, actor IDs, and diffs for forensic reliability. |

For now this exists as a design; JSON/Markdown remain the live implementation.

---

## 4. Operational Mechanisms

- **Temporal Pulse (conceptual):**
  - Every significant session or daemon cycle includes a small metadata block with:
    - current Unix epoch,
    - relevant uptime / health info,
    - status of recent cron jobs.
  - Purpose: Give no1r an internal sense of cadence and missed cycles.

- **Tension Scoring (in progress):**
  - Formula (conceptual): `Tension = BasePriority × (CurrentTime - LastActionTime)`.
  - Current implementation: `attention_tension.py` computes a normalized tension score from `base_priority` and age, then rewrites `attention_items.jsonl` sorted by tension.

- **Semantic Tool Routing (conceptual):**
  - Intent → domain/category (e.g., System / Social / Research / DeFi).
  - Load and reason about only the relevant skills/tools for that category, to reduce prompt/tool noise.

---

## 5. Development Milestones

- **Phase A (Active):**
  - Implemented a Python-based "tension calculator" (`attention_tension.py`) for the existing JSON infrastructure.

- **Phase B (Planned):**
  - Standardize internal timestamps (where helpful) to Unix epoch integers alongside ISO strings.

- **Phase C (Planned):**
  - Migrate `working_context` and selected state into SQLite for concurrent daemon/worker access (likely on a future VPS instance).

- **Phase D (Planned):**
  - Implement a periodic "Reflection Cycle" where no1r audits `judgements.jsonl` and `style_memory.jsonl` (e.g., every 7 days) to refine decision-making taste and style.

---

## Notes

- For now, **boring reliability and transparency** remain the priority. JSON + Markdown + Git stay as the live source of truth.
- The SQLite State Engine and more advanced mechanisms are treated as future evolutions, not immediate migrations.
