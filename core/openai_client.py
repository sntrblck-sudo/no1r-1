"""Lightweight OpenAI client wrapper (optional). Uses AsyncOpenAI if available.
This file is a safe integration point — it only attempts to call the provider if OPENAI_API_KEY is set.
"""
import os
import logging
from typing import List, Dict, Any

log = logging.getLogger('noir.openai')
OPENAI_KEY = os.environ.get('OPENAI_API_KEY')

try:
    from openai import AsyncOpenAI
    ASYNC_AVAILABLE = True
except Exception:
    AsyncOpenAI = None
    ASYNC_AVAILABLE = False

async def async_call_model(model: str, messages: List[Dict[str, Any]], max_tokens: int=128) -> Dict[str,Any]:
    if not OPENAI_KEY:
        raise RuntimeError('OPENAI_API_KEY not set; aborting live call')
    if not ASYNC_AVAILABLE:
        raise RuntimeError('AsyncOpenAI SDK not available in this environment')
    client = AsyncOpenAI(api_key=OPENAI_KEY)
    resp = await client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens)
    # Minimal normalization
    return {'content': resp.choices[0].message.content, 'usage': getattr(resp, 'usage', None)}

def call_model_sync_stub(model: str, messages: List[Dict[str,Any]], max_tokens: int=128) -> Dict[str,Any]:
    # Fallback stub when no API key or SDK is present — returns a deterministic placeholder
    prompt = '\n'.join(m.get('content','') for m in messages)
    summary = f"[stub reply from {model} — {len(prompt)} chars]"
    return {'content': summary, 'usage': None}
