BLOCKPAY INTEGRATION PLAN — safe, review-first flow

Goal
- Allow no1r-2 to prepare draft invoices and payment proposals for BlockPay, but require no1r-1/operator review and explicit human actions for any real-world payment or wallet connection. Preserve auditability and avoid direct agent-led financial actions.

Principles
- Read-only for agents by default: no direct wallet connections, no sending invoices, no marking paid.  
- Elevation-first: no1r-2 writes fully-formed `draft_invoice` objects to `exchange` for no1r-1 review.  
- Human gate: no1r-1 (or operator) must perform any external action (Send invoice, Connect wallet, Refund).  
- Audit trail: every draft and decision recorded in core/history with timestamps and commit ids.

Data flows
1) Input sources
   - Business data (client name, email, amount, token preference) lives in experiments/inputs or core/shared_memory.yaml as read-only fields.  
   - No direct access to any private keys or wallet secrets.

2) Drafting pipeline (no1r-2)
   - Validate brief and required fields (client, amount, due date, token).  
   - If fields missing, emit a defer/clarify `SimulationReport`.  
   - If sufficient, produce a `DraftInvoice` JSON and place it at `exchange/drafts/draft_<id>.json` with schema: {job_id, client, amount, token_choices, due_date, line_items, notes, recommended_action, confidence, audit_reference}.
   - Add `watch_items` if token choice includes risky tokens (new or low-liquidity) or if amount exceeds thresholds.

3) Elevation & review (no1r-1)
   - no1r-1 monitors exchange/drafts/ and receives elevation messages.  
   - no1r-1 inspects draft, may edit through the UI or command, and must manually execute any human-only action (Send invoice, Connect wallet).  
   - When sending, operator follows OPERATOR_HEAL_CHECKLIST-style steps for finance: confirm receiving address, token, and network manually.

Safety controls
- No credential storage: do not store any wallet private keys; only store receiving addresses as non-sensitive metadata.  
- Human-only actions enforced by policy and technical limits: agents lack API keys or OAuth tokens needed to perform payments.  
- Rate limits for draft generation to avoid spam: max 10 drafts per hour per agent.  
- Require `confidence` field; auto-accept only for > 0.9 under supervised test mode (not in production).

Audit & logging
- Each draft and decision is committed to git under exchange/ with a stable filename; core/history logs the decision and operator who acted.  
- Maintain a payment ledger copy in experiments/payments/ for operator tracking (simulated until operator marks real payment).

Implementation checklist (developer)
- [ ] Define DraftInvoice JSON schema and validator.  
- [ ] Implement no1r-2 draft generator (read-only mode).  
- [ ] Add exchange/drafts/ watcher and notification to no1r-1.  
- [ ] Implement a small admin UI or CLI for no1r-1 to edit/approve drafts.  
- [ ] Add rate-limits and confidence thresholds.  
- [ ] Log and audit hooks (core/history updates) on approval.

Next steps (proposal)
- Prototype: implement DraftInvoice generation for one job type and test locally.  
- Review: present drafts to operator (no1r-1) for UX feedback.  
- Deploy: harden logging and enforce no-credential guarantees before enabling in production.
