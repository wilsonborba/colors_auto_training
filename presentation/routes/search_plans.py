from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from presentation.handlers.response_dto import PresentationResponseDTO
from presentation.handlers.search_handler import SearchPlanHandler

router = APIRouter(tags=["search-plans"])


class CreateSearchPlanRequest(BaseModel):
    query: str = Field(..., min_length=1)
    source_type: str = Field(default="manual", pattern="^(manual|groq)$")
    video_source_id: str | None = None
    keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)


class RejectSearchPlanRequest(BaseModel):
    reason: str | None = None


class StartAutomaticRequest(BaseModel):
    query: str | None = None
    video_source_id: str | None = None
    seed_keywords: list[str] = Field(default_factory=list)


class ReviewSearchResultRequest(BaseModel):
    reason: str | None = None


class BulkSearchPlanRequest(BaseModel):
    plan_ids: list[str] = Field(default_factory=list)
    action: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def get_search_plan_handler() -> SearchPlanHandler:
    return SearchPlanHandler()


def _to_http(response_dto: PresentationResponseDTO) -> JSONResponse:
    return JSONResponse(status_code=response_dto.status_code, content=response_dto.to_dict())


@router.post("/search-plans")
def create_search_plan_route(request: CreateSearchPlanRequest) -> JSONResponse:
    return _to_http(get_search_plan_handler().create_plan(request.model_dump()))


@router.post("/search-plans/{plan_id}/run")
def run_search_plan_route(plan_id: str) -> JSONResponse:
    return _to_http(get_search_plan_handler().run_plan(plan_id))


@router.post("/search-plans/auto-start")
def auto_start_search_plan_route(request: StartAutomaticRequest) -> JSONResponse:
    return _to_http(get_search_plan_handler().start_automatic(request.model_dump()))


@router.get("/search-plans")
def list_search_plans_route() -> JSONResponse:
    return _to_http(get_search_plan_handler().list_plans())


@router.get("/search-plans/{plan_id}")
def get_search_plan_route(plan_id: str) -> JSONResponse:
    return _to_http(get_search_plan_handler().get_plan(plan_id))


@router.get("/search-plans/{plan_id}/results")
def get_search_plan_results_route(plan_id: str) -> JSONResponse:
    return _to_http(get_search_plan_handler().get_plan_results(plan_id))


@router.post("/search-plans/{plan_id}/approve")
def approve_search_plan_route(plan_id: str, request: RejectSearchPlanRequest) -> JSONResponse:
    return _to_http(get_search_plan_handler().approve_plan(plan_id, request.reason))


@router.post("/search-plans/{plan_id}/reject")
def reject_search_plan_route(plan_id: str, request: RejectSearchPlanRequest) -> JSONResponse:
    return _to_http(get_search_plan_handler().reject_plan(plan_id, request.reason))


@router.post("/search-results/{result_id}/approve")
def approve_search_result_route(result_id: str, request: ReviewSearchResultRequest) -> JSONResponse:
    return _to_http(get_search_plan_handler().review_result(result_id, True, request.reason))


@router.post("/search-results/{result_id}/reject")
def reject_search_result_route(result_id: str, request: ReviewSearchResultRequest) -> JSONResponse:
    return _to_http(get_search_plan_handler().review_result(result_id, False, request.reason))


@router.post("/search-plans/bulk")
def bulk_search_plan_action_route(request: BulkSearchPlanRequest) -> JSONResponse:
    return _to_http(get_search_plan_handler().bulk_action(request.plan_ids, request.action))
