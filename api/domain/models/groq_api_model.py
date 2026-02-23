from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GroqResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
