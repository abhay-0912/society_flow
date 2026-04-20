from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    import json
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)
