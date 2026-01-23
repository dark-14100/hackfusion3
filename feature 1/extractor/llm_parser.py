import json
from typing import Dict, Any, List

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"  # change if you use a different model

client = httpx.Client(timeout=120.0)


def _call_ollama(prompt: str) -> Dict[str, Any]:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }
    resp = client.post(OLLAMA_URL, json=payload)
    resp.raise_for_status()
    return resp.json()


def _build_prompt(user_text: str) -> str:
    return f"""
You are a pharmacy assistant. Extract medicine orders from the user's text
and return STRICT JSON only. Do not include any explanation.

User text:
\"\"\"{user_text}\"\"\"


Return JSON with this shape:

{{
  "medicines": [
    {{
      "raw_name": "<the medicine name phrase as user said it>",
      "canonical_name": "<normalized medicine name in English>",
      "strength": "<e.g. '500mg' or '20 mg/ml'> or null",
      "form": "<e.g. 'tablet', 'capsule', 'drops'> or null",
      "frequency": "<e.g. 'once daily', 'twice daily', 'three times daily'> or null",
      "duration": "<e.g. '5 days', '2 weeks'> or null",
      "quantity": <integer or null>
    }}
  ]
}}

Rules:
- If you are not sure about a field, use null.
- quantity is the total number of units requested (e.g. 10 tablets -> 10).
- If no medicines are mentioned, return {{ "medicines": [] }}.
- Respond with JSON only, no backticks, no extra text.
""".strip()


def llm_extract_order(user_text: str) -> Dict[str, Any]:
    prompt = _build_prompt(user_text)
    raw = _call_ollama(prompt)

    # Ollama's /generate response body has a "response" field containing the model text
    # Adjust if your Ollama version returns a different field.
    model_text = raw.get("response") or raw.get("output") or ""
    model_text = model_text.strip()

    # Sometimes the model may wrap JSON with text; try to locate the JSON object.
    # For hackathon speed: assume it's valid top-level JSON.
    try:
        parsed = json.loads(model_text)
    except json.JSONDecodeError:
        # Very simple recovery: try to extract between first { and last }
        start = model_text.find("{")
        end = model_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(model_text[start : end + 1])
        else:
            # If completely unusable, return empty result so caller falls back to rule-based output.
            return {"medicines": []}

    # Ensure expected shape
    meds = parsed.get("medicines", [])
    if not isinstance(meds, list):
        meds = []

    # Normalize each medicine dict (ensure keys exist)
    normalized_meds: List[Dict[str, Any]] = []
    for m in meds:
        if not isinstance(m, dict):
            continue
        normalized_meds.append(
            {
                "raw_name": m.get("raw_name"),
                "canonical_name": m.get("canonical_name"),
                "strength": m.get("strength"),
                "form": m.get("form"),
                "frequency": m.get("frequency"),
                "duration": m.get("duration"),
                "quantity": m.get("quantity"),
            }
        )

    return {"medicines": normalized_meds}