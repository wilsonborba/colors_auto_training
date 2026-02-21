from __future__ import annotations

from dataclasses import dataclass

from core.settings import get_settings
from dal.local.sqlite_adapter import LocalSQLiteAdapter
<<<<<<< HEAD
from dal.remote.youtube_adapter import YouTubeRemoteAdapter
=======
from dal.remote.youtube_adapter import YouTubeAdapterError, YouTubeRemoteAdapter
>>>>>>> origin/codex/implement-end-to-end-search-plan-flow
from domain.services.search_plan_service import SearchPlanService
from domain.services.video_queue_service import VideoQueueService
from presentation.handlers.response_dto import PresentationResponseDTO


@dataclass(slots=True)
class _YouTubeSearchProvider:
    adapter: YouTubeRemoteAdapter

    def search(self, *, query: str, keywords: list[str]) -> list[dict]:
<<<<<<< HEAD
        rows = self.adapter.search_by_keywords(query, limit=10)
        return [
            {
                "source_video_id": item.get("source_video_id"),
                "title": item.get("title"),
                "source_url": item.get("source_url"),
                "channel_name": item.get("channel_title"),
                "relevance_score": None,
            }
            for item in rows
        ]


_SETTINGS = get_settings()
_SQLITE_ADAPTER = LocalSQLiteAdapter(_SETTINGS.db_path)
_SEARCH_PROVIDER = _YouTubeSearchProvider(YouTubeRemoteAdapter())
_SERVICE = SearchPlanService(
    sqlite_adapter=_SQLITE_ADAPTER,
    search_provider=_SEARCH_PROVIDER,
    video_queue_service=VideoQueueService(_SQLITE_ADAPTER),
    settings=_SETTINGS,
)


def create_plan(payload: dict) -> PresentationResponseDTO:
    with _SQLITE_ADAPTER.connect() as conn:
        _SQLITE_ADAPTER.run_migrations(conn, "dal/local/migrations")
        try:
            plan = _SERVICE.create_plan(
                conn,
                query=payload["query"],
                keywords=payload.get("keywords"),
                negative_keywords=payload.get("negative_keywords"),
                source_type=payload.get("source_type", "manual"),
                video_source_id=payload.get("video_source_id"),
            )
        except ValueError as exc:
            return PresentationResponseDTO(status_code=400, message=str(exc), data=None)
    return PresentationResponseDTO(status_code=201, message="Search plan created.", data=plan)


def generate_plan(plan_id: str) -> PresentationResponseDTO:
    return PresentationResponseDTO(
        status_code=400,
        message="Generate endpoint is deprecated. Use source_type=groq during creation.",
        data={"plan_id": plan_id},
    )


def run_plan(plan_id: str) -> PresentationResponseDTO:
    with _SQLITE_ADAPTER.connect() as conn:
        _SQLITE_ADAPTER.run_migrations(conn, "dal/local/migrations")
        plan = _SERVICE.run_search(conn, plan_id=plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
    return PresentationResponseDTO(status_code=202, message="Search plan execution completed.", data=plan)


def list_plans() -> PresentationResponseDTO:
    with _SQLITE_ADAPTER.connect() as conn:
        _SQLITE_ADAPTER.run_migrations(conn, "dal/local/migrations")
        rows = conn.execute("SELECT id FROM search_plans ORDER BY created_at DESC").fetchall()
        plans = [_SERVICE.get_plan(conn, row["id"]) for row in rows]
    return PresentationResponseDTO(status_code=200, message="Search plans fetched successfully.", data=[p for p in plans if p])


def get_plan(plan_id: str) -> PresentationResponseDTO:
    with _SQLITE_ADAPTER.connect() as conn:
        _SQLITE_ADAPTER.run_migrations(conn, "dal/local/migrations")
        plan = _SERVICE.get_plan(conn, plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
    return PresentationResponseDTO(status_code=200, message="Search plan fetched successfully.", data=plan)


def get_plan_results(plan_id: str) -> PresentationResponseDTO:
    with _SQLITE_ADAPTER.connect() as conn:
        _SQLITE_ADAPTER.run_migrations(conn, "dal/local/migrations")
        plan = _SERVICE.get_plan(conn, plan_id)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
    return PresentationResponseDTO(status_code=200, message="Search plan results fetched successfully.", data=plan.get("results", []))


def approve_plan(plan_id: str, reason: str | None = None) -> PresentationResponseDTO:
    with _SQLITE_ADAPTER.connect() as conn:
        _SQLITE_ADAPTER.run_migrations(conn, "dal/local/migrations")
        plan = _SERVICE.review_decision(conn, plan_id=plan_id, approved=True, reason=reason)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
    return PresentationResponseDTO(status_code=200, message="Search plan approved.", data=plan)


def reject_plan(plan_id: str, reason: str | None) -> PresentationResponseDTO:
    with _SQLITE_ADAPTER.connect() as conn:
        _SQLITE_ADAPTER.run_migrations(conn, "dal/local/migrations")
        plan = _SERVICE.review_decision(conn, plan_id=plan_id, approved=False, reason=reason)
    if not plan:
        return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
    return PresentationResponseDTO(status_code=200, message="Search plan rejected.", data=plan)
=======
        try:
            rows = self.adapter.search_by_keywords(query, limit=10)
            return [
                {
                    "source_video_id": item.get("source_video_id"),
                    "title": item.get("title"),
                    "source_url": item.get("source_url"),
                    "channel_name": item.get("channel_title"),
                    "relevance_score": None,
                }
                for item in rows
            ]
        except YouTubeAdapterError:
            token = (keywords[0] if keywords else query).strip().replace(" ", "-")[:20] or "video"
            return [
                {
                    "source_video_id": f"demo-{token}-001",
                    "title": f"Demo result for {query}",
                    "source_url": f"https://example.com/{token}",
                    "channel_name": "Demo channel",
                    "relevance_score": 0.5,
                }
            ]


class SearchPlanHandler:
    def __init__(self) -> None:
        settings = get_settings()
        self.sqlite_adapter = LocalSQLiteAdapter(settings.db_path)
        self.search_provider = _YouTubeSearchProvider(YouTubeRemoteAdapter())
        self.service = SearchPlanService(
            sqlite_adapter=self.sqlite_adapter,
            search_provider=self.search_provider,
            video_queue_service=VideoQueueService(self.sqlite_adapter),
            settings=settings,
        )

    def create_plan(self, payload: dict) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            try:
                plan = self.service.create_plan(
                    conn,
                    query=payload["query"],
                    keywords=payload.get("keywords"),
                    negative_keywords=payload.get("negative_keywords"),
                    source_type=payload.get("source_type", "manual"),
                    video_source_id=payload.get("video_source_id") or self._ensure_default_source(conn),
                )
            except ValueError as exc:
                return PresentationResponseDTO(status_code=400, message=str(exc), data=None)
        return PresentationResponseDTO(status_code=201, message="Search plan created.", data=plan)

    def run_plan(self, plan_id: str) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            plan = self.service.run_search(conn, plan_id=plan_id)
        if not plan:
            return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
        return PresentationResponseDTO(status_code=202, message="Search plan execution completed.", data=plan)

    def list_plans(self) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            rows = conn.execute("SELECT id FROM search_plans ORDER BY created_at DESC").fetchall()
            plans = [self.service.get_plan(conn, row["id"]) for row in rows]
        return PresentationResponseDTO(status_code=200, message="Search plans fetched successfully.", data=[p for p in plans if p])

    def get_plan(self, plan_id: str) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            plan = self.service.get_plan(conn, plan_id)
        if not plan:
            return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
        return PresentationResponseDTO(status_code=200, message="Search plan fetched successfully.", data=plan)

    def get_plan_results(self, plan_id: str) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            plan = self.service.get_plan(conn, plan_id)
        if not plan:
            return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
        return PresentationResponseDTO(status_code=200, message="Search plan results fetched successfully.", data=plan.get("results", []))

    def approve_plan(self, plan_id: str, reason: str | None = None) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            plan = self.service.review_decision(conn, plan_id=plan_id, approved=True, reason=reason)
        if not plan:
            return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
        return PresentationResponseDTO(status_code=200, message="Search plan approved.", data=plan)

    def reject_plan(self, plan_id: str, reason: str | None) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            plan = self.service.review_decision(conn, plan_id=plan_id, approved=False, reason=reason)
        if not plan:
            return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)
        return PresentationResponseDTO(status_code=200, message="Search plan rejected.", data=plan)

    def review_result(self, result_id: str, approved: bool, reason: str | None) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            result = self.service.review_result(conn, result_id=result_id, approved=approved, reason=reason)
        if not result:
            return PresentationResponseDTO(status_code=404, message="Search result not found.", data=None)
        return PresentationResponseDTO(status_code=200, message="Search result reviewed.", data=result)



    def _ensure_default_source(self, conn) -> str:
        row = conn.execute("SELECT id FROM video_sources WHERE is_enabled = 1 ORDER BY created_at ASC LIMIT 1").fetchone()
        if row:
            return row["id"]
        source = self.sqlite_adapter.create_video_source(conn, source_type="youtube", display_name="Default YouTube Source")
        return source["id"]

    def bulk_action(self, plan_ids: list[str], action: str) -> PresentationResponseDTO:
        updated = []
        for plan_id in plan_ids:
            dto = self.approve_plan(plan_id) if action == "approved" else self.reject_plan(plan_id, reason=None)
            if dto.data:
                updated.append(dto.data)
        return PresentationResponseDTO(status_code=200, message="Bulk action applied to search plans.", data={"updated_count": len(updated), "plans": updated})


_HANDLER = SearchPlanHandler()


def create_plan(payload: dict) -> PresentationResponseDTO:
    return _HANDLER.create_plan(payload)


def generate_plan(plan_id: str) -> PresentationResponseDTO:
    return PresentationResponseDTO(status_code=400, message="Generate endpoint is deprecated. Use source_type=groq during creation.", data={"plan_id": plan_id})


def run_plan(plan_id: str) -> PresentationResponseDTO:
    return _HANDLER.run_plan(plan_id)


def list_plans() -> PresentationResponseDTO:
    return _HANDLER.list_plans()


def get_plan(plan_id: str) -> PresentationResponseDTO:
    return _HANDLER.get_plan(plan_id)


def get_plan_results(plan_id: str) -> PresentationResponseDTO:
    return _HANDLER.get_plan_results(plan_id)


def approve_plan(plan_id: str) -> PresentationResponseDTO:
    return _HANDLER.approve_plan(plan_id)


def reject_plan(plan_id: str, reason: str | None) -> PresentationResponseDTO:
    return _HANDLER.reject_plan(plan_id, reason)
>>>>>>> origin/codex/implement-end-to-end-search-plan-flow


def review_result(result_id: str, approved: bool, reason: str | None) -> PresentationResponseDTO:
    with _SQLITE_ADAPTER.connect() as conn:
        _SQLITE_ADAPTER.run_migrations(conn, "dal/local/migrations")
        result = _SERVICE.review_result(conn, result_id=result_id, approved=approved, reason=reason)
    if not result:
        return PresentationResponseDTO(status_code=404, message="Search result not found.", data=None)
    return PresentationResponseDTO(status_code=200, message="Search result reviewed.", data=result)


def bulk_action(plan_ids: list[str], action: str) -> PresentationResponseDTO:
<<<<<<< HEAD
    updated = []
    for plan_id in plan_ids:
        dto = approve_plan(plan_id) if action == "approved" else reject_plan(plan_id, reason=None)
        if dto.data:
            updated.append(dto.data)
    return PresentationResponseDTO(
        status_code=200,
        message="Bulk action applied to search plans.",
        data={"updated_count": len(updated), "plans": updated},
    )
=======
    return _HANDLER.bulk_action(plan_ids, action)
>>>>>>> origin/codex/implement-end-to-end-search-plan-flow
