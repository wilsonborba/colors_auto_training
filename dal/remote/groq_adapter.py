from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class GroqAdapterError(Exception):
    pass


class GroqDisabledError(GroqAdapterError):
    pass


class GroqResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class GroqKeywordPlanner:
    api_key: str
    model: str
    base_url: str = "https://api.groq.com/openai/v1"
    timeout_seconds: float = 20.0

    def create_plan(self, user_query: str) -> GroqResponseSchema:
        prompt = (
            "Create a safe video search plan as strict JSON only. "
            "Schema: {\"query\": string, \"keywords\": string[], \"negative_keywords\": string[]}. "
            "Include negative keywords to reduce irrelevant results. "
            "Never create sexual, explicit, pornographic, child, toddler, kid, schoolgirl, teen, underage, or minors-focused intent. "
            "If user input is unsafe, sanitize it to a benign alternative query."
        )
        response_text = self._chat([
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_query},
        ])

        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise GroqAdapterError("Groq did not return valid JSON.") from exc

        try:
            return GroqResponseSchema.model_validate(payload)
        except ValidationError as exc:
            raise GroqAdapterError(f"Groq response failed schema validation: {exc}") from exc

    def _chat(self, messages: list[dict[str, str]]) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        body = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": messages,
        }
        req = request.Request(
            url,
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            raise GroqAdapterError(f"Groq HTTP error: {exc.code}") from exc
        except error.URLError as exc:
            raise GroqAdapterError(f"Groq connection error: {exc.reason}") from exc

        try:
            parsed = json.loads(raw)
            return parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise GroqAdapterError("Malformed Groq completion response.") from exc
