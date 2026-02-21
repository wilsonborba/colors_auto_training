from __future__ import annotations

from presentation.handlers.response_dto import PresentationResponseDTO


class JobsEventsHandler:
    def __init__(self) -> None:
        self._active_jobs = [
            {"id": "job-1", "type": "training", "status": "running"},
            {"id": "job-2", "type": "search", "status": "queued"},
        ]
        self._events = [
            {"id": "event-1", "type": "job.started", "payload": {"job_id": "job-1"}},
            {"id": "event-2", "type": "job.queued", "payload": {"job_id": "job-2"}},
        ]

    def get_active_jobs(self) -> PresentationResponseDTO:
        return PresentationResponseDTO(
            status_code=200,
            message="Active jobs fetched successfully.",
            data=self._active_jobs,
        )

    def tail_events(self, limit: int) -> PresentationResponseDTO:
        return PresentationResponseDTO(
            status_code=200,
            message="Event tail fetched successfully.",
            data=self._events[-limit:] if limit > 0 else [],
        )
