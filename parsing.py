"""Normalize LLM response content and extract structured JSON from it."""

import json
import re


def extract_text(content) -> str:
  """Normalize LangChain content (str or list-of-parts) to plain text."""
  if isinstance(content, list):
    return "".join(
        p.get("text", "") if isinstance(p, dict) else str(p) for p in content
    )
  return content


def extract_json(text) -> dict:
  """Unwrap LangChain content parts, then pull out the JSON object.

  Handles three shapes the model's response might arrive in:
  1. A real list of content parts (e.g. [{"type": "text", "text": "..."}]).
  2. A string that is itself a serialized version of that list.
  3. A plain string, possibly with markdown fences or extra prose around
     the JSON object.
  """
  if isinstance(text, list):
    text = extract_text(text)

  stripped = text.strip()
  if stripped.startswith("["):
    try:
      parts = json.loads(stripped)
      if isinstance(parts, list):
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except json.JSONDecodeError:
      pass

  match = re.search(r"\{.*\}", text, re.DOTALL)
  if not match:
    raise ValueError("No JSON object found in model response")
  return json.loads(match.group(0))
