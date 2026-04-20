from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _fallback_classification(message: str) -> dict:
    lower = message.lower()
    if any(word in lower for word in ["paani", "water", "leak", "tap", "pipe"]):
        category = "plumbing"
    elif any(word in lower for word in ["light", "electric", "power", "switch", "corridor"]):
        category = "electrical"
    elif any(word in lower for word in ["clean", "garbage", "trash", "waste"]):
        category = "cleaning"
    elif any(word in lower for word in ["security", "guard", "gate", "theft"]):
        category = "security"
    elif any(word in lower for word in ["noise", "loud", "shor", "awaaz"]):
        category = "noise"
    else:
        category = "other"

    return {
        "category": category,
        "priority": "medium",
        "summary": message[:120],
        "reply": "Thanks for reporting this. We have logged your complaint and our team will assist shortly.",
    }


def classify_complaint(message: str) -> dict:
    prompt = f"""
You are an AI assistant for a housing society management system.
A resident has sent this message: "{message}"

Classify it and reply ONLY with this JSON format, nothing else:
{{
  "category": "plumbing|electrical|cleaning|security|noise|other",
  "priority": "low|medium|high",
  "summary": "one line summary in English",
  "reply": "a short friendly reply in the same language as the message"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        raw = (response.choices[0].message.content or "").strip()
        return json.loads(raw)
    except Exception:
        # Keep webhook responsive even if OpenAI fails.
        return _fallback_classification(message)
