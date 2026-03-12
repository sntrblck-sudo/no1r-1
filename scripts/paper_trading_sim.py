#!/usr/bin/env python3
"""Accelerated paper trading sim (7-day prototype) with balance-aware sizing and conservative defaults.
Environment overrides: SEED_BALANCE, MAX_PCT_PER_TRADE, RESERVE_FRAC, MIN_CONFIDENCE, MAX_TRADES_DAY
"""
import random, json, os
from datetime import datetime
from pathlib import Path

WS=Path('/home/sntrblck/.openclaw/workspace')
STATE_FILE=WS/'finance_state.json'
OUT_DIR=WS/'experiments'/'simulations'/'paper_trading'
OUT_DIR.mkdir(parents=True,exist_ok=True)

SEED_BAL=float(os.environ.get('SEED_BALANCE', '500'))
MAX_PCT_PER_TRADE=float(os.environ.get('MAX_PCT_PER_TRADE','0.005'))  # 0.5% per trade
RESERVE_FRAC=float(os.environ.get('RESERVE_FRAC','0.15'))
MIN_CONF=float(os.environ.get('MIN_CONFIDENCE','0.65'))
MAX_TRADES_DAY=int(os.environ.get('MAX_TRADES_DAY','8'))


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

report={'start':datetime.utcnow().isoformat()+'Z','days':[],'start_balance':state.get('balance_sim',0),'params':{'seed':SEED_BAL,'max_pct':MAX_PCT_PER_TRADE,'reserve':RESERVE_FRAC,'min_conf':MIN_CONF,'max_trades_day':MAX_TRADES_DAY}}

for day in range(7):
    trades_today=0
    day_record={'day':day+1,'trades':[],'balance_start':round(state['balance_sim'],2)}
    # up to MAX_TRADES_DAY attempts
    for attempt in range(MAX_TRADES_DAY):
        # simulate getting a confidence score
        confidence=random.uniform(0.4,0.95)
        if confidence < MIN_CONF:
            action='skip_low_conf'
            note='skipped due to low confidence'
            day_record['trades'].append({'action':action,'confidence':round(confidence,2),'note':note,'balance':round(state['balance_sim'],2)})
            continue
        price_move=random.uniform(-0.05,0.05)
        trade_action=random.choice(['buy','sell','hold'])
        trade_size_pct=random.uniform(0.001, MAX_PCT_PER_TRADE)
        trade_amount=round(state['balance_sim']*trade_size_pct,2)
        revenue=0
        cost=0
        note='no trade'
        if trade_action=='buy' and trade_amount>0:
            cost=round(trade_amount * (1+abs(price_move)) * 0.01,6)
            reserve=RESERVE_FRAC * state['balance_sim']
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
        day_record['trades'].append({'action':trade_action,'trade_amount':trade_amount,'cost':cost,'revenue':revenue,'confidence':round(confidence,2),'note':note,'balance':round(state['balance_sim'],2)})
        trades_today += 1
    # simulate daily overhead
    if state.get('balance_sim',0) >= state.get('monthly_vps_cost',5):
        state['balance_sim'] -= state.get('monthly_vps_cost',5)/30
    day_record['balance_end']=round(state['balance_sim'],2)
    report['days'].append(day_record)

save_state(state)
outf=OUT_DIR/f'paper_trading_report_{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
outf.write_text(json.dumps(report,indent=2))
print('Wrote',outf)
print('End balance:',state['balance_sim'])
