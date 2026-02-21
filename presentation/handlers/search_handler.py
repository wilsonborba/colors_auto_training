from __future__ import annotations

from dataclasses import dataclass
from threading import Thread

from core.settings import get_settings
from dal.local.sqlite_adapter import LocalSQLiteAdapter
from dal.remote.youtube_adapter import YouTubeAdapterError, YouTubeRemoteAdapter
from domain.services.search_plan_service import SearchPlanService
from domain.services.video_queue_service import VideoQueueService
from presentation.handlers.response_dto import PresentationResponseDTO


@dataclass(slots=True)
class _YouTubeSearchProvider:
    adapter: YouTubeRemoteAdapter

    def search(self, *, query: str, keywords: list[str]) -> list[dict]:
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
    _AUTO_SEED_KEYWORDS = [
        "street interview",
        "city walking tour",
        "public places",
        "crowd vlog",
        "daily life downtown",
        "people fashion",
        "mall walkthrough",
        "festival crowd",
        "commuter station",
        "market street",
    ]

    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
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

    def start_automatic(self, payload: dict) -> PresentationResponseDTO:
        if not self.settings.groq_plan_generation_enabled:
            return PresentationResponseDTO(
                status_code=400,
                message="Automatic mode requires Groq plan generation to be enabled in settings.",
                data=None,
            )

        query = (payload.get("query") or "videos with many visible people in public places").strip()
        seed_keywords = payload.get("seed_keywords") or self._AUTO_SEED_KEYWORDS
        seed_phrase = ", ".join(f'"{keyword}"' for keyword in seed_keywords)
        prompt_query = (
            f"{query}. Return keywords focused on videos with many visible persons on YouTube. "
            f"Start from this seed list: {seed_phrase}."
        )

        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            try:
                plan = self.service.create_plan(
                    conn,
                    query=prompt_query,
                    source_type="groq",
                    video_source_id=payload.get("video_source_id") or self._ensure_default_source(conn),
                )
                conn.execute(
                    "UPDATE search_plans SET status = 'running', updated_at = ? WHERE id = ?",
                    (self.sqlite_adapter.utc_now_iso(), plan["id"]),
                )
                self.sqlite_adapter.append_event(
                    conn,
                    event_type="search_plan.run.queued",
                    aggregate_type="search_plan",
                    aggregate_id=plan["id"],
                    payload={"search_plan_id": plan["id"], "mode": "automatic"},
                )
            except ValueError as exc:
                return PresentationResponseDTO(status_code=400, message=str(exc), data=None)

        Thread(target=self._run_plan_async, args=(plan["id"],), daemon=True).start()
        return PresentationResponseDTO(
            status_code=202,
            message="Automatic search started with AI-generated keywords.",
            data={"plan_id": plan["id"]},
        )

    def run_plan(self, plan_id: str) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            plan = self.service.get_plan(conn, plan_id)
            if not plan:
                return PresentationResponseDTO(status_code=404, message="Search plan not found.", data=None)

            conn.execute(
                "UPDATE search_plans SET status = 'running', updated_at = ? WHERE id = ?",
                (self.sqlite_adapter.utc_now_iso(), plan_id),
            )
            self.sqlite_adapter.append_event(
                conn,
                event_type="search_plan.run.queued",
                aggregate_type="search_plan",
                aggregate_id=plan_id,
                payload={"search_plan_id": plan_id},
            )

        Thread(target=self._run_plan_async, args=(plan_id,), daemon=True).start()
        return PresentationResponseDTO(status_code=202, message="Search plan execution started asynchronously.", data={"plan_id": plan_id})

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

    def _run_plan_async(self, plan_id: str) -> None:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")

            def _emit(progress: dict) -> None:
                self.sqlite_adapter.append_event(
                    conn,
                    event_type=f"search_plan.run.{progress.get('stage', 'progress')}",
                    aggregate_type="search_plan",
                    aggregate_id=plan_id,
                    payload=progress,
                )

            self.service.run_search(conn, plan_id=plan_id, auto_enqueue=True, progress_callback=_emit)

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


def bulk_action(plan_ids: list[str], action: str) -> PresentationResponseDTO:
    return _HANDLER.bulk_action(plan_ids, action)
