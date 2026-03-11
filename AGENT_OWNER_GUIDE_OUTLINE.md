# Agent Owner Guide (Outline)

**Working title:** Designing Your First Agent (Safely)

Audience: Non-technical people who want a personal/ops-style agent, not a trading bot.

Goal: Give them mental models, safety rails, and a simple path to a useful, non-chaotic agent.

---

## 1. What an Agent Actually Is

- Not just a chatbot
  - Difference between “ask it a question” vs “it runs persistently in the background.”
- Basic architecture (plain language)
  - Brain: model (LLM)
  - Hands: tools (email, calendar, files, messaging, etc.)
  - Memory: files, logs, notes
  - Nerves: triggers (cron, events, webhooks)
- Key idea: **autonomy = loops + tools + memory**, not just IQ.

---

## 2. Safety First: Boundaries Before Brains

- What can go wrong (non-scary, but honest)
  - Spamming people or channels
  - Deleting/overwriting data
  - Moving money
  - Saying things you didn’t intend
- Safe defaults
  - Read-only for most tools at first
  - No access to real funds or critical systems
  - You as the approval step for anything irreversible
- The “three rings” model:
  - Ring 1: safe to automate (notes, summaries, reminders)
  - Ring 2: suggest but don’t execute (emails, posts, config changes)
  - Ring 3: never automate (money, destructive actions)

---

## 3. Designing Your Agent’s Personality & Role

- Role first, personality second
  - Decide: ops assistant? research helper? social summarizer?
  - Avoid “do everything” – it becomes chaotic.
- Simple disposition file
  - Example structure (inspired by `DISPOSITION.md`):
    - Core stance (e.g. quiet, ops-first)
    - Hard NOs (never do without explicit ask)
    - Always-ok actions
    - When to notify you
- Examples
  - "Ops brain" like no1r
  - "Research digest" agent
  - "Calendar & commitments" agent

---

## 4. Ops Basics for Non-Ops People

- Health checks in human language
  - "Is it alive?" – process/service status
  - "Is it listening?" – can it receive messages/requests?
  - "Is it responding correctly?" – a quick sanity check.
- Heartbeats and logs
  - Why periodic logs are good
  - Why log spam is bad
- Minimal ops stack
  - One status command (like `ops_inbox.py`)
  - One state file (`ops_state.json`) with simple OK/WARN flags
  - One panic playbook (what to do if things feel off)

---

## 5. Memory & Concept Layers

- Raw vs curated
  - Daily notes / transcripts vs long-term memory
- Concept layer (like `CONCEPTS.md`)
  - Where you write down “how we operate” patterns
  - Example: "Noise is a failure mode" for alerts
- Teaching your agent over time
  - Updating personality/ops/policy docs
  - Reflecting on incidents and near-misses

---

## 6. Autonomy, Gradually

- Start with **pull-only**
  - You ask, agent responds
- Then **safe push**
  - Agent can notify you:
    - “Here’s your daily summary”
    - “Something looks off with X (non-destructive)”
- Then **small loops**
  - Safe cron jobs: backups, summaries, log cleanup
  - Still no changes to money or critical systems
- Always have a path back
  - How to disable/stop the agent
  - How to roll back a change

---

## 7. Common Patterns to Copy

- Personal ops brain
  - Watches your tools/logs, summarizes status
- Project sentinel
  - Watches one project’s repos/notes/tasks
- Social summarizer
  - Summarizes specific channels or feeds (but doesn’t post without you)

---

## 8. What NOT to Do (Yet)

- No trading bots or auto-farmers
- No auto-sending emails or DMs on your behalf
- No direct access to banking/fiat accounts
- No giving it your main password manager or root keys

---

## 9. Growing With Confidence

- Signs you can safely do more
  - Weeks of boring reliability
  - Few surprises in behavior
  - Clear playbooks and logs
- How to add one new capability at a time
  - A new tool, a new trigger, or a new narrow role
  - Never all three at once

---

## 10. Next Steps

- Turn this into:
  - a short guide or mini-course
  - templates for DISPOSITION / OPS_POLICY / PANIC_PLAYBOOK
- Optional: example repo showcasing a minimal agent setup (like no1rlocal, but generic).
