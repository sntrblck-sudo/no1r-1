"""Drop-in wrapper to integrate cost precheck into routing calls.
Provides call_with_precheck(task_type, messages, budget_cap_usd, primary, fallback)
Also can execute the chosen model (async if OpenAI client present) and reconcile actual usage.
"""
from core.model_cost_precheck import should_call, estimate_cost_usd
from core import openai_client
import json
from pathlib import Path
import asyncio

LOG=Path('/home/sntrblck/.openclaw/workspace/experiments/metrics')
LOG.mkdir(parents=True,exist_ok=True)


def _write_log(rec: dict):
    fname=LOG/f'router_decision_{__import__("datetime").datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
    fname.write_text(json.dumps(rec,indent=2))


def call_with_precheck_and_call(task_type, messages, budget_cap_usd, primary, fallback=None, out_tokens=128):
    ok,est = should_call(primary,messages,budget_cap_usd,out_tokens)
    chosen=None
    reason=None
    est_used=est
    if ok:
        chosen=primary
        reason='primary_within_budget'
    else:
        if fallback:
            ok2,est2 = should_call(fallback,messages,budget_cap_usd,out_tokens)
            if ok2:
                chosen=fallback
                reason='fallback_within_budget'
                est_used=est2
            else:
                chosen=None
                reason='all_over_budget'
        else:
            chosen=None
            reason='primary_over_budget_no_fallback'
    # Precheck log
    rec={'ts':__import__('datetime').datetime.utcnow().isoformat()+'Z','phase':'precheck','task_type':str(task_type),'primary':primary,'fallback':fallback,'chosen':chosen,'est_usd':est_used,'budget_cap_usd':budget_cap_usd,'reason':reason}
    _write_log(rec)

    if chosen is None:
        return {'ok':False,'reason':reason}

    # Execute the model call if possible; use async client if available, otherwise a stub
    actual=None
    usage=None
    try:
        if openai_client.OPENAI_KEY and openai_client.ASYNC_AVAILABLE:
            # run async call
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # can't run nested loop; use new loop
                new_loop = asyncio.new_event_loop()
                actual = new_loop.run_until_complete(openai_client.async_call_model(chosen,messages,out_tokens))
            else:
                actual = loop.run_until_complete(openai_client.async_call_model(chosen,messages,out_tokens))
            usage = actual.get('usage',None)
        else:
            actual = openai_client.call_model_sync_stub(chosen,messages,out_tokens)
    except Exception as e:
        _write_log({'ts':__import__('datetime').datetime.utcnow().isoformat()+'Z','phase':'call_error','error':str(e)})
        return {'ok':False,'reason':'call_failed','error':str(e)}

    # Post-call reconciliation log
    post={'ts':__import__('datetime').datetime.utcnow().isoformat()+'Z','phase':'postcall','task_type':str(task_type),'model_used':chosen,'est_usd':est_used,'usage':usage,'cached':False}
    _write_log(post)

    return {'ok':True,'model':chosen,'result':actual,'est_usd':est_used,'usage':usage}
