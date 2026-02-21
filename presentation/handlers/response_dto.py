from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PresentationResponseDTO:
    """Shared response envelope returned by presentation handlers."""

    status_code: int
    message: str
    data: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "message": self.message,
            "data": self.data,
        }
