from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from uuid import UUID


@dataclass
class KeywordModel:
    id: UUID
    key_name: str
    created_at: str

    def to_dict(self):
        return asdict(self)
