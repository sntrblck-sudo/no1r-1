"""Drop-in wrapper to integrate cost precheck into routing calls.
Provides call_with_precheck(task_type, messages, budget_cap_usd, primary, fallback)
This is a light wrapper — the real router can replace its call sites with this function.
"""
from core.model_cost_precheck import should_call, estimate_cost_usd
import json
from pathlib import Path
LOG=Path('/home/sntrblck/.openclaw/workspace/experiments/metrics')
LOG.mkdir(parents=True,exist_ok=True)


def call_with_precheck(task_type, messages, budget_cap_usd, primary, fallback=None, out_tokens=128):
    ok,est = should_call(primary,messages,budget_cap_usd,out_tokens)
    chosen=None
    reason=None
    if ok:
        chosen=primary
        reason='primary_within_budget'
    else:
        if fallback:
            ok2,est2 = should_call(fallback,messages,budget_cap_usd,out_tokens)
            if ok2:
                chosen=fallback
                reason='fallback_within_budget'
            else:
                chosen=None
                reason='all_over_budget'
        else:
            chosen=None
            reason='primary_over_budget_no_fallback'
    # Log the decision
    rec={'ts':__import__('datetime').datetime.utcnow().isoformat()+'Z','task_type':str(task_type),'primary':primary,'fallback':fallback,'chosen':chosen,'est_usd':est,'budget_cap_usd':budget_cap_usd,'reason':reason}
    fname=LOG/f'router_decision_{__import__("datetime").datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
    fname.write_text(json.dumps(rec,indent=2))
    return chosen, reason, est
