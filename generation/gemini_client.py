"""Gemini Flash wrapper -- Tier 3 (complex reasoning, multimodal, long context)."""
import os
from loguru import logger

_model = None


def _get_model():
    global _model
    if _model is None:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        _model = genai.GenerativeModel("gemini-1.5-flash")
    return _model


def generate(prompt: str, max_tokens: int = 1200) -> dict:
    model = _get_model()
    resp = model.generate_content(prompt, generation_config={"max_output_tokens": max_tokens, "temperature": 0.1})
    usage = resp.usage_metadata
    logger.info(f"Gemini generate: {usage.prompt_token_count} in / {usage.candidates_token_count} out")
    return {
        "answer": resp.text,
        "model": "gemini-2.5-flash",
        "tokens_in": usage.prompt_token_count,
        "tokens_out": usage.candidates_token_count,
    }
