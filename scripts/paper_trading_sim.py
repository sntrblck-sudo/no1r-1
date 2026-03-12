#!/usr/bin/env python3
"""Accelerated paper trading sim (7-day prototype) with balance-aware sizing and seed float.
Updates finance_state.json (simulated) and writes a report to experiments/simulations/paper_trading/
Usage: set SEED_BALANCE env var or defaults to 100
"""
import random, json, os
from datetime import datetime, timedelta
from pathlib import Path

WS=Path('/home/sntrblck/.openclaw/workspace')
STATE_FILE=WS/'finance_state.json'
OUT_DIR=WS/'experiments'/'simulations'/'paper_trading'
OUT_DIR.mkdir(parents=True,exist_ok=True)

SEED_BAL=float(os.environ.get('SEED_BALANCE', '100'))
MAX_PCT_PER_TRADE=float(os.environ.get('MAX_PCT_PER_TRADE','0.02'))  # 2% per trade


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return { 'balance_sim': SEED_BAL, 'daily_spent':0, 'monthly_vps_cost':5.0 }


def save_state(s):
    STATE_FILE.write_text(json.dumps(s,indent=2))

state=load_state()
# seed if starting from zero
if state.get('balance_sim',0) <= 0:
    state['balance_sim']=SEED_BAL

report={'start':datetime.utcnow().isoformat()+'Z','days':[],'start_balance':state.get('balance_sim',0)}

for day in range(7):
    # simulate market moves and a single small trade decision
    price_move=random.uniform(-0.05,0.05)
    trade_action=random.choice(['buy','sell','hold'])
    # size as percentage of current balance
    trade_size_pct=random.uniform(0.001, MAX_PCT_PER_TRADE)  # 0.1% to MAX
    trade_amount=round(state['balance_sim']*trade_size_pct,2)
    revenue=0
    cost=0
    note='no trade'
    if trade_action=='buy' and trade_amount>0:
        cost=round(trade_amount * (1+abs(price_move)) * 0.01,6)
        # only allow buy if it won't breach reserve (5% reserve)
        reserve=0.05 * state['balance_sim']
        if state['balance_sim'] - cost >= reserve:
            state['balance_sim'] -= cost
            note=f'buy simulated, cost {cost:.2f}'
        else:
            note='buy skipped (would breach reserve)'
    elif trade_action=='sell' and trade_amount>0:
        revenue=round(trade_amount * (1+price_move) * 0.02,6)
        state['balance_sim'] += revenue
        note=f'sell simulated, revenue {revenue:.2f}'
    else:
        note='hold'
    # simulate daily overhead
    if state.get('balance_sim',0) >= state.get('monthly_vps_cost',5):
        state['balance_sim'] -= state.get('monthly_vps_cost',5)/30

    report['days'].append({'day':day+1,'action':trade_action,'trade_amount':trade_amount,'cost':cost,'revenue':revenue,'note':note,'balance':round(state['balance_sim'],2)})

save_state(state)
outf=OUT_DIR/f'paper_trading_report_{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
outf.write_text(json.dumps(report,indent=2))
print('Wrote',outf)
print('End balance:',state['balance_sim'])
