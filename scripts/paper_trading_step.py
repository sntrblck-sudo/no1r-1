#!/usr/bin/env python3
"""One-step paper trading action: run a single trading cycle (one 'day' step) using current finance_state.json
This is intended to be invoked repeatedly by a scheduler to simulate real-time paper trading.
Adds judgement-layer audit fields to each trade record.
"""
import random, json
from datetime import datetime
from pathlib import Path

WS=Path('/home/sntrblck/.openclaw/workspace')
STATE_FILE=WS/'finance_state.json'
OUT_DIR=WS/'experiments'/'simulations'/'paper_trading'
OUT_DIR.mkdir(parents=True,exist_ok=True)

# conservative defaults
MAX_PCT_PER_TRADE=0.0025  # 0.25%
RESERVE_FRAC=0.15
MIN_CONF=0.65
MAX_TRADES_DAY=8

JUDGMENT_MODEL='v0.1-heuristic'

if not STATE_FILE.exists():
    state={'balance_sim':500.0,'daily_spent':0,'monthly_vps_cost':5.0}
else:
    state=json.loads(STATE_FILE.read_text())

trades_executed=0
day_record={'ts':datetime.utcnow().isoformat()+'Z','trades':[],'balance_start':round(state['balance_sim'],2)}
for attempt in range(MAX_TRADES_DAY):
    # Simulated judgment-layer output
    confidence=random.uniform(0.4,0.95)
    judgement_score=round(confidence,2)
    judgement_reason='sim_confidence'

    if confidence < MIN_CONF:
        day_record['trades'].append({'action':'skip_low_conf','confidence':round(confidence,2),'judgment':{'score':judgement_score,'model':JUDGMENT_MODEL,'reason':judgement_reason}})
        continue
    action=random.choice(['buy','sell','hold'])
    trade_pct=random.uniform(0.0005, MAX_PCT_PER_TRADE)
    amount=round(state['balance_sim']*trade_pct,2)
    cost=0; revenue=0
    if action=='buy' and amount>0:
        cost=round(amount*0.01,6)
        reserve=RESERVE_FRAC*state['balance_sim']
        if state['balance_sim'] - cost >= reserve:
            state['balance_sim'] -= cost
            note='buy'
        else:
            note='buy_skipped_reserve'
    elif action=='sell' and amount>0:
        revenue=round(amount*0.02,6)
        state['balance_sim'] += revenue
        note='sell'
    else:
        note='hold'

    trade_entry={'action':note,'amount':amount,'cost':cost,'revenue':revenue,'confidence':round(confidence,2),'balance':round(state['balance_sim'],2),'judgment':{'score':judgement_score,'model':JUDGMENT_MODEL,'reason':judgement_reason}}
    day_record['trades'].append(trade_entry)
    trades_executed += 1

# overhead
if state.get('balance_sim',0) >= state.get('monthly_vps_cost',5):
    state['balance_sim'] -= state.get('monthly_vps_cost',5)/30

state['last_updated']=datetime.utcnow().isoformat()+'Z'
STATE_FILE.write_text(json.dumps(state,indent=2))

outf=OUT_DIR/f'paper_trading_step_{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
outf.write_text(json.dumps(day_record,indent=2))
print('wrote',outf)
print('balance',state['balance_sim'])
