from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from presentation.handlers.response_dto import PresentationResponseDTO
from presentation.handlers.video_queue_handler import VideoQueueHandler

router = APIRouter(tags=["video-queue"])


class UpdatePriorityRequest(BaseModel):
    priority: int = Field(..., ge=0)


@lru_cache(maxsize=1)
def get_video_queue_handler() -> VideoQueueHandler:
    return VideoQueueHandler()


def _to_http(response_dto: PresentationResponseDTO) -> JSONResponse:
    return JSONResponse(status_code=response_dto.status_code, content=response_dto.model_dump())


@router.get("/videos")
def list_videos() -> JSONResponse:
    return _to_http(get_video_queue_handler().list_videos())


@router.post("/videos/{video_id}/priority")
def update_video_priority(video_id: str, request: UpdatePriorityRequest) -> JSONResponse:
    return _to_http(get_video_queue_handler().update_priority(video_id, request.priority))


@router.post("/videos/{video_id}/retry")
def retry_video(video_id: str) -> JSONResponse:
    return _to_http(get_video_queue_handler().retry_video(video_id))


@router.post("/videos/{video_id}/disable")
def disable_video(video_id: str) -> JSONResponse:
    return _to_http(get_video_queue_handler().disable_video(video_id))


@router.post("/videos/{video_id}/enable")
def enable_video(video_id: str) -> JSONResponse:
    return _to_http(get_video_queue_handler().enable_video(video_id))
