from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Query
from starlette.responses import JSONResponse

from presentation.handlers.jobs_events_handler import JobsEventsHandler
from presentation.handlers.response_dto import PresentationResponseDTO

router = APIRouter(tags=["jobs-events"])


@lru_cache(maxsize=1)
def get_jobs_events_handler() -> JobsEventsHandler:
    return JobsEventsHandler()


def _to_http(response_dto: PresentationResponseDTO) -> JSONResponse:
    return JSONResponse(status_code=response_dto.status_code, content=response_dto.model_dump())


@router.get("/jobs/active")
def get_active_jobs() -> JSONResponse:
    return _to_http(get_jobs_events_handler().get_active_jobs())


@router.get("/events/tail")
def tail_events(limit: int = Query(default=50, ge=1, le=500)) -> JSONResponse:
    return _to_http(get_jobs_events_handler().tail_events(limit))
