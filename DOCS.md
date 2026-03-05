# DOCS INDEX

Quick map of the important documentation files in this workspace.

---

## Core Identity & Behavior

- `SOUL.md` – Core behavior, tone, and operating principles for no1r.
- `IDENTITY.md` – Name, vibe, and visual identity.
- `USER.md` – Notes about you (preferences, guardrails, priorities).
- `DISPOSITION.md` – Operational stance and boundaries (hard NOs, always-OK actions).

Read when: you want to remember how this agent is supposed to behave.

---

## Ops & Safety

- `OPS_POLICY.md` – What "OK" means for Gateway, Sentinel, and Cron.
- `PANIC_PLAYBOOK.md` – Step-by-step commands to run if something feels wrong.
- `CONCEPTS.md` – Reusable ideas/patterns learned over time (e.g., alert noise, MoltX behavior).

Read when: you want to check health, respond to issues, or refine ops behavior.

---

## Autonomy & Judgement

- `judgements.jsonl` – JSONL log of significant decisions and their self-judgements (correctness, conservatism, noise).
- `AGENT_OWNER_GUIDE_OUTLINE.md` – Outline for a guide teaching non-technical people to own and customize their agents safely.

Read when: you want to see how decisions are being evaluated or to evolve the agent owner guide.

---

## Ops Tools & Scripts (entry points)

- `ops_inbox.py` – One-shot ops snapshot (Gateway + Sentinel + Cron) and write to `ops_state.json`.
- `base_wallet_snapshot.py` – Read-only BaseScan snapshot for your Base wallet (requires `BASESCAN_API_KEY`).
- `judgement_log.py` – Seeds/extends `judgements.jsonl` with structured decision entries.

Run when: you want quick status (`ops_inbox.py`) or fresh Base wallet state, or when growing the judgement log.

---

## Git & Ignore Rules

- `.gitignore` – Ensures logs and state files stay out of the repo:
  - `*.log`, `*_state.json`, `.model-health-state.json`, `base_wallet_state.json`, `ops_state.json`, `judgements.jsonl`, future `events.jsonl`, `posts.jsonl`.

Check when: adding new scripts that create logs/state, to keep the repo clean.

---

This file is a living index – update it when new long-lived docs or entry points are added.
