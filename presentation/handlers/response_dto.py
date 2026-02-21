from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PresentationResponseDTO(BaseModel):
    """Shared response envelope returned by all presentation handlers."""

    status_code: int
    message: str
    data: Any | None = None
