from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from presentation.handlers.response_dto import PresentationResponseDTO
from presentation.handlers.video_queue_handler import (
    disable_video,
    enable_video,
    list_videos,
    retry_video,
    update_priority,
)

router = APIRouter(tags=["video-queue"])


class UpdatePriorityRequest(BaseModel):
    priority: int = Field(..., ge=0)


def _to_http(response_dto: PresentationResponseDTO) -> JSONResponse:
    return JSONResponse(status_code=response_dto.status_code, content=response_dto.to_dict())


@router.get("/videos")
def list_videos_route() -> JSONResponse:
    return _to_http(list_videos())


@router.post("/videos/{video_id}/priority")
def update_video_priority(video_id: str, request: UpdatePriorityRequest) -> JSONResponse:
    return _to_http(update_priority(video_id, request.priority))


@router.post("/videos/{video_id}/retry")
def retry_video_route(video_id: str) -> JSONResponse:
    return _to_http(retry_video(video_id))


@router.post("/videos/{video_id}/disable")
def disable_video_route(video_id: str) -> JSONResponse:
    return _to_http(disable_video(video_id))


@router.post("/videos/{video_id}/enable")
def enable_video_route(video_id: str) -> JSONResponse:
    return _to_http(enable_video(video_id))
