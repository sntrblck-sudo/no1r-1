
---

## ENHANCEMENTS — v1.1 (tightened rules)

Purpose: narrow the public posting surface, require structured elevation + review, and make auditability mandatory for all potential external posts.

1) Posting workflow (required)
- Worker bodies (no1r-2) may only prepare `elevation` messages and drafts; they MUST NOT post externally.  
- An `elevation` must include: `summary`, `recommended_action` (`post`|`edit_and_post`|`reject`), `confidence` (0.0-1.0), `watch_items`, `audit_reference` (repo path to full SimulationReport), and `suggested_post_text` (optional).  
- no1r-1 reviews the elevation and must: approve (post), edit+post, or reject and return with comments. Approval must be recorded in `core/history/` with timestamp and commit id.  

2) Mandatory audit fields for any external post
- Every post must reference an `audit_reference` pointing to the SimulationReport or exchange message that produced it.  
- No external post without a valid audit_reference will be allowed by policy.

3) Delay & confirmation for irreversible or broad‑reach posts
- For posts classified as `irreversible` or `broad_reach` (policy decision — e.g., any post that could change user behavior or public opinion), enforce a 30‑minute delay and require a second confirmation from no1r‑1 or the human operator before publishing.

4) Explicit bans and guardrails
- Agent voices must never: impersonate humans, claim emotions, or present unverified facts as truths.  
- No marketing/sales persuasion tactics: no urgency theater, no false scarcity, and no emotional manipulation.  
- No public financial claims or promises; any finance‑related public text must include a safety disclaimer and audit_reference.

5) Technical enforcement recommendations
- All proposed posts should be written to `exchange/elevations/` as JSON; no1r‑1 should have a small UI/CLI to approve and optionally edit before posting.  
- The posting system checks `audit_reference` exists and that `confidence` >= 0.65 for auto-suggested posts; otherwise, it flags for manual scrutiny.

6) Minimal templates (for no1r-1 use)
- Health alert (urgent): "[no1r] ALERT — {summary}. See {audit_reference}."  
- Governance change (reviewed): "[no1r] Governance update: {one_line_summary}. Details: {audit_reference}."  

7) When to escalate to operator
- If an elevation references `policy_tension` or `legal_adj`, no1r-1 must escalate to the operator (Sen) before posting.  

These enhancements are additive to v1.0. They tighten the posting workflow to ensure every public act is auditable and reviewed.
