from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from uuid import UUID

from api.domain.models.keyword import KeywordModel

Status = Literal["QUEUED", "PROCESSING", "COMPLETED", "FAILED"]


@dataclass
class VideoModel:
    id: UUID
    keyword_id: KeywordModel
    name: str

    created_at: str
    status: Status
    url_link: str

    def to_dict(self):
        return asdict(self)


@dataclass
class VideoLogModel:
    id: UUID
    video_id: VideoModel
    timestamp: str
    message: str

    def to_dict(self):
        return asdict(self)


@
