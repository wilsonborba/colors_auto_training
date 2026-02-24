from dataclasses import asdict, dataclass
from uuid import UUID


@dataclass
class KeywordModel:
    id: UUID
    key_name: str
    query_search: str
    created_at: str
    videos_extracted: bool

    def to_dict(self):
        return asdict(self)
