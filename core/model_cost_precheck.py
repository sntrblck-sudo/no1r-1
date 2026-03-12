"""Simple cost precheck utilities for noir router
Estimate token usage roughly and compute cost based on model pricing table.
"""
from typing import List
import hashlib

# minimal pricing table (USD per 1M tokens input+output)
PRICING = {
    'gpt-4.1-nano': 0.10+0.40,
    'gpt-4o-mini': 0.15+0.60,
    'gpt-4.1-mini': 0.40+1.60,
    'gpt-4.1': 2.00+8.00,
}

def rough_token_count(messages: List[dict]) -> int:
    # extremely coarse heuristic: 1 token per 4 chars
    total_chars = 0
    for m in messages:
        total_chars += len(m.get('content',''))
    return max(1, total_chars // 4)

def estimate_cost_usd(model: str, messages: List[dict], out_tokens: int=128) -> float:
    tokens = rough_token_count(messages) + out_tokens
    per_m = PRICING.get(model, 1.0)  # default price if unknown
    return (tokens/1_000_000) * per_m

def should_call(model: str, messages: List[dict], budget_cap_usd: float, out_tokens: int=128) -> (bool, float):
    est = estimate_cost_usd(model, messages, out_tokens=out_tokens)
    return (est <= budget_cap_usd, est)
