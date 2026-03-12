"""Model registry and routing table for noir.
Defines pricing and routing defaults for TaskTypes.
"""
from enum import Enum

PRICING = {
    'gpt-4.1-nano': 0.10+0.40,
    'gpt-4o-mini': 0.15+0.60,
    'gpt-4.1-mini': 0.40+1.60,
    'gpt-4.1': 2.00+8.00,
    'o4-mini': 1.10+4.40,
    'o3': 10.00+40.00,
    'gpt-code-mini': 0.50+2.00
}

# Simple routing defaults by task (recommended set)
ROUTING_TABLE = {
    'social_post': {'model':'gpt-4o-mini','fallback':'gpt-4.1-mini'},
    'social_comment': {'model':'gpt-4.1-nano','fallback':'gpt-4o-mini'},
    'social_sentiment': {'model':'gpt-4.1-nano','fallback':'gpt-4o-mini'},
    'judgment_eval': {'model':'gpt-4o-mini','fallback':'gpt-4.1-mini'},
    'prompt_injection': {'model':'gpt-4.1-nano','fallback':'gpt-4o-mini'},
    'task_planning': {'model':'gpt-4.1-mini','fallback':'gpt-4.1'},
    'self_improvement': {'model':'o4-mini','fallback':'gpt-4.1'},
    'market_signal': {'model':'gpt-4.1-nano','fallback':'gpt-4o-mini'},
    'trade_reasoning': {'model':'o4-mini','fallback':'o3'},
    'summarise': {'model':'gpt-4.1-nano','fallback':'gpt-4o-mini'},
    'classify': {'model':'gpt-4.1-nano','fallback':'gpt-4o-mini'},
    'code_small': {'model':'gpt-code-mini','fallback':'o4-mini'},
    'code_complex': {'model':'o4-mini','fallback':'o3'},
}
