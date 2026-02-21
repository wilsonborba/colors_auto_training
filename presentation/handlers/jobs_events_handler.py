from __future__ import annotations

from presentation.handlers.response_dto import PresentationResponseDTO

_ACTIVE_JOBS = [
    {"id": "job-1", "type": "training", "status": "running"},
    {"id": "job-2", "type": "search", "status": "queued"},
]

_EVENTS = [
    {"id": "event-1", "type": "job.started", "payload": {"job_id": "job-1"}},
    {"id": "event-2", "type": "job.queued", "payload": {"job_id": "job-2"}},
]


class JobsEventsHandler:
    """Maps jobs/events read operations into presentation DTOs."""

    def get_active_jobs(self) -> PresentationResponseDTO:
        return PresentationResponseDTO(
            status_code=200,
            message="Active jobs fetched successfully.",
            data=_ACTIVE_JOBS,
        )

    def tail_events(self, limit: int) -> PresentationResponseDTO:
        return PresentationResponseDTO(
            status_code=200,
            message="Event tail fetched successfully.",
            data=_EVENTS[-limit:] if limit > 0 else [],
        )
