from __future__ import annotations

from presentation.handlers.response_dto import PresentationResponseDTO

_VIDEOS: dict[str, dict] = {
    "vid-1": {"id": "vid-1", "priority": 1, "enabled": True, "retries": 0},
    "vid-2": {"id": "vid-2", "priority": 2, "enabled": True, "retries": 1},
}


def list_videos() -> PresentationResponseDTO:
    return PresentationResponseDTO(
        status_code=200,
        message="Video queue fetched successfully.",
        data=list(_VIDEOS.values()),
    )


def update_priority(video_id: str, priority: int) -> PresentationResponseDTO:
    video = _VIDEOS.get(video_id)
    if not video:
        return PresentationResponseDTO(status_code=404, message="Video not found.", data=None)

    video["priority"] = priority
    return PresentationResponseDTO(status_code=200, message="Video priority updated.", data=video)


def retry_video(video_id: str) -> PresentationResponseDTO:
    video = _VIDEOS.get(video_id)
    if not video:
        return PresentationResponseDTO(status_code=404, message="Video not found.", data=None)

    video["retries"] += 1
    return PresentationResponseDTO(status_code=200, message="Video retry scheduled.", data=video)


def disable_video(video_id: str) -> PresentationResponseDTO:
    video = _VIDEOS.get(video_id)
    if not video:
        return PresentationResponseDTO(status_code=404, message="Video not found.", data=None)

    video["enabled"] = False
    return PresentationResponseDTO(status_code=200, message="Video disabled.", data=video)


def enable_video(video_id: str) -> PresentationResponseDTO:
    video = _VIDEOS.get(video_id)
    if not video:
        return PresentationResponseDTO(status_code=404, message="Video not found.", data=None)

    video["enabled"] = True
    return PresentationResponseDTO(status_code=200, message="Video enabled.", data=video)
