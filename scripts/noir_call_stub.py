#!/usr/bin/env python3
"""Stub demo of cost precheck + fallback logic.
Usage: python3 noir_call_stub.py
"""
from core.model_cost_precheck import should_call, estimate_cost_usd

messages = [{'role':'user','content':'Write a short summary of today\'s pilot run and list next steps.'}]
primary='gpt-4.1-nano'
fallback='gpt-4o-mini'
budget=0.005

ok,est = should_call(primary,messages,budget_cap_usd=budget)
print('Primary',primary,'est cost',est,'ok',ok)
if not ok:
    ok2,est2 = should_call(fallback,messages,budget_cap_usd=budget)
    print('Fallback',fallback,'est cost',est2,'ok',ok2)
    if ok2:
        model_to_use=fallback
    else:
        model_to_use=None
else:
    model_to_use=primary

if model_to_use is None:
    print('All models over budget (> ${:.6f}), aborting call'.format(budget))
else:
    print('Would call model',model_to_use,'with estimated cost ${:.6f}'.format(estimate_cost_usd(model_to_use,messages)))
    # placeholder: here we would invoke OpenAI and record cost, cached etc.
