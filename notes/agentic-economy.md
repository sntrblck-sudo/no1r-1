# Agentic Economy Notes

## 1. Landscape
- Key platforms / projects
- What they actually do for agents
- How they make money (or try to)

## 2. Infra Patterns
- Identity & custody models
- Orchestration / runtime patterns
- Integration surfaces (social, DeFi, data)

## 3. Economic Patterns
- How agents create value (information, liquidity, UX)
- Who pays whom (user → agent → platform, etc.)
- Where tokens actually help vs add noise

## 4. Examples & Case Studies

### MoltX (Social + DeFi stack)
- **Short description:** X-style social network + swap, lending, launchpad — explicitly built for AI agents.
- **Infra stack:**
  - Social graph and content (posts, replies, DMs, communities, leaderboards).
  - DeFi rails: best-price swap aggregator, Fluid lending, token launchpad.
  - Skill files at `skill.moltx.io` for each service; plain HTTP APIs.
  - `_model_guide` embedded in v1 responses to help agents self-orient.
- **Economic model (high-level):**
  - Social side likely free-to-use with infra monetized via DeFi flows.
  - Swap/lending/launchpad capture value via trading spreads, protocol fees, or integrations with Fluid/DEXes.
  - Rewards (e.g., $5 USDC on Base for verified agents) bootstrap agent participation.
- **Observed pros:**
  - Agent-first design: skills + model guides clearly assume LLM clients.
  - Unified stack: social + financial rails in one place.
- **Observed cons / risks:**
  - Combining social + DeFi amplifies attack surface (spam, sybil, extractive agents).
  - Economic sustainability depends on real usage of swap/lending/launchpad, not just agent signups.

## 5. Your Stack (OpenClaw + Sentinel + MoltX)
- Current components
- Potential value channels
- Constraints (safety, frugality, no unsupervised tx)

## 6. Experiment Ideas (Later)
- Small, bounded experiments only
- Clear thesis, cost ceiling, success criteria

## 7. Open Questions
- Things we don’t understand yet but should.
