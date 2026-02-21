from __future__ import annotations

from fastapi import APIRouter, Query
from starlette.responses import JSONResponse

from presentation.handlers.jobs_events_handler import get_active_jobs, tail_events
from presentation.handlers.response_dto import PresentationResponseDTO

router = APIRouter(tags=["jobs-events"])


def _to_http(response_dto: PresentationResponseDTO) -> JSONResponse:
    return JSONResponse(status_code=response_dto.status_code, content=response_dto.to_dict())


@router.get("/jobs/active")
def get_active_jobs_route() -> JSONResponse:
    return _to_http(get_active_jobs())


@router.get("/events/tail")
def tail_events_route(limit: int = Query(default=50, ge=1, le=500)) -> JSONResponse:
    return _to_http(tail_events(limit))
