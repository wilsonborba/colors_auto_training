from __future__ import annotations

import json
from dataclasses import dataclass

import requests
from core.utils.errors import GroqAdapterError
from domain.models.groq_api_model import GroqResponseSchema
from pydantic import ValidationError


@dataclass(slots=True)
class GroqApiAdapter:
    api_key: str
    model: str
    base_url: str = "https://api.groq.com/openai/v1"
    timeout_seconds: float = 20.0

    def query(self, user_query: str, prompt: str) -> GroqResponseSchema:
        response_text = self._chat(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_query},
            ]
        )

        # The model's message content is expected to be a JSON string
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise GroqAdapterError(
                "Groq did not return valid JSON in message content."
            ) from exc

        try:
            return GroqResponseSchema.model_validate(payload)
        except ValidationError as exc:
            raise GroqAdapterError(
                f"Groq response failed schema validation: {exc}"
            ) from exc

    def _chat(self, messages: list[dict[str, str]]) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        body = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                url,
                json=body,  # requests will JSON-encode and set content-type (we keep header explicit anyway)
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise GroqAdapterError(
                f"Groq request timed out after {self.timeout_seconds}s."
            ) from exc
        except requests.RequestException as exc:
            # Covers connection errors, DNS, etc.
            raise GroqAdapterError(f"Groq connection error: {exc}") from exc

        # Convert non-2xx into a nice error (with body if possible)
        if not resp.ok:
            detail = None
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text[:500]  # avoid dumping huge HTML pages
            raise GroqAdapterError(f"Groq HTTP error {resp.status_code}: {detail}")

        try:
            parsed = resp.json()
            return parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            # ValueError here is JSON decode error from resp.json()
            raise GroqAdapterError("Malformed Groq completion response.") from exc
