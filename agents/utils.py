"""Shared utilities: Anthropic client init and JSON parsing."""

import json
import os
import re

from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"


def get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and add your key, then run: "
            "  export $(cat .env | xargs)  (Linux/Mac)\n"
            "  set /p ANTHROPIC_API_KEY=<.env  (Windows, rough equivalent)"
        )
    return Anthropic(api_key=api_key)


def parse_json(text: str, agent_name: str = "Agent") -> dict:
    """
    Robustly extract a JSON object from an LLM response.
    Handles plain JSON, markdown code fences, and responses with preamble text.
    """
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Markdown code fence  ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. First top-level { … } block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"[{agent_name}] Could not parse JSON from response.\n"
        f"First 600 chars:\n{text[:600]}"
    )
