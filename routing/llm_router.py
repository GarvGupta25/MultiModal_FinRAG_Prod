"""Routes a built prompt to the correct model based on classified tier."""
import os
from routing.complexity_classifier import classify_query
from generation.groq_client import generate as groq_generate
from generation.gemini_client import generate as gemini_generate

TIER2_MODEL = os.environ.get("GROQ_TIER2_MODEL", "llama-3.3-70b-versatile")


def route_and_generate(query: str, prompt: str, has_image_ref: bool = False) -> dict:
    tier = classify_query(query, has_image_ref=has_image_ref)

    if tier == 1:
        result = groq_generate(prompt, model="llama-3.1-8b-instant")
    elif tier == 2:
        result = groq_generate(prompt, model=TIER2_MODEL)
    else:
        try:
            result = gemini_generate(prompt)
        except Exception:
            # graceful fallback if Gemini key/quota fails -- don't break the query
            result = groq_generate(prompt, model=TIER2_MODEL)
            tier = 2

    result["tier"] = tier
    return result
