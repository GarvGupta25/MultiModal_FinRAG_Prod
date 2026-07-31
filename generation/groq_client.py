"""Groq API wrapper. Tier 1 (llama-3.1-8b-instant) for Stage 1; Tier 2 model added in Stage 2."""
import os
from loguru import logger

_client = None


def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def generate(prompt: str, model: str = "llama-3.1-8b-instant", max_tokens: int = 800) -> dict:
    client = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.1,
    )
    answer = resp.choices[0].message.content
    usage = resp.usage
    logger.info(f"Groq generate via {model}: {usage.prompt_tokens} in / {usage.completion_tokens} out")
    return {
        "answer": answer,
        "model": model,
        "tokens_in": usage.prompt_tokens,
        "tokens_out": usage.completion_tokens,
    }
