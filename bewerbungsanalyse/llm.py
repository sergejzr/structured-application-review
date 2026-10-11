from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import requests


class LLMClient:
    """OpenAI-kompatibler Client, standardmäßig für OpenWebUI."""

    def __init__(self) -> None:
        base = os.environ.get("OPENWEBUI_API_BASE", "").rstrip("/")
        self.api_key = os.environ.get("OPENWEBUI_API_KEY", "")
        self.model = os.environ.get("OPENWEBUI_MODEL", "")
        if not all((base, self.api_key, self.model)):
            raise RuntimeError(
                "OPENWEBUI_API_BASE, OPENWEBUI_API_KEY und OPENWEBUI_MODEL müssen gesetzt sein"
            )
        self.url = base if base.endswith("/chat/completions") else base + "/chat/completions"

    def complete_json(self, system: str, user: str, max_tokens: int = 12000) -> dict[str, Any]:
        content = self.complete_text(system, user, max_tokens)
        value = parse_json(content)
        if not isinstance(value, dict):
            raise ValueError("LLM-Antwort ist kein JSON-Objekt")
        return value

    def complete_text(self, system: str, user: str, max_tokens: int = 12000) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0,
            "max_tokens": max_tokens,
            # DeepSeek in OpenWebUI kann sonst das gesamte Ausgabebudget fürs
            # Reasoning verbrauchen und content leer zurückgeben.
            "reasoning_effort": "none",
        }
        last_error: Exception | None = None
        for attempt in range(5):
            try:
                response = requests.post(
                    self.url,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=(20, 900),
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("LLM-Antwort enthält keinen Text")
                return content.strip()
            except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
                last_error = exc
                if attempt < 4:
                    time.sleep(3 * (2**attempt))
        raise RuntimeError(f"LLM-Aufruf fehlgeschlagen: {last_error}")


def parse_json(text: str) -> Any:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        starts = [(cleaned.find("{"), "}"), (cleaned.find("["), "]")]
        starts = [(start, close) for start, close in starts if start >= 0]
        if not starts:
            raise
        start, close = min(starts)
        return json.loads(cleaned[start : cleaned.rfind(close) + 1])
