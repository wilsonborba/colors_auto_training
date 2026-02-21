from __future__ import annotations

import re
import sqlite3
from typing import Any, Iterable, Protocol

from core.settings import Settings
from dal.local.sqlite_adapter import LocalSQLiteAdapter
from dal.remote.groq_adapter import GroqKeywordPlanner
from domain.services.video_queue_service import VideoQueueService


class SearchProviderPort(Protocol):
    def search(self, *, query: str, keywords: list[str]) -> Iterable[dict[str, Any]]: ...


class SearchPlanService:
    """Creates plans, runs remote search, and applies review decisions."""

    _UNSAFE_TERMS = {
        "sex", "sexual", "porn", "explicit", "erotic", "nude", "nudity",
        "child", "children", "kid", "kids", "underage", "minor", "schoolgirl", "toddler", "teen",
    }

    def __init__(
        self,
        sqlite_adapter: LocalSQLiteAdapter,
        search_provider: SearchProviderPort,
        video_queue_service: VideoQueueService,
        settings: Settings,
    ) -> None:
        self.sqlite_adapter = sqlite_adapter
        self.search_provider = search_provider
        self.video_queue_service = video_queue_service
        self.settings = settings
        self.groq_planner = self._build_groq_planner(settings)

    def create_plan(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        keywords: list[str] | None = None,
        negative_keywords: list[str] | None = None,
        source_type: str = "manual",
        video_source_id: str | None = None,
    ) -> dict[str, Any]:
        generated_query = query
        positive_keywords = list(keywords or [])
        negative = list(negative_keywords or [])

        if source_type == "groq" and self.groq_planner:
            groq_plan = self.groq_planner.create_plan(query)
            generated_query = groq_plan.query
            positive_keywords = groq_plan.keywords
            negative = groq_plan.negative_keywords

        self._validate_safety(generated_query, positive_keywords + negative)

        plan = self.sqlite_adapter.create_search_plan(
            conn,
            query=generated_query,
            video_source_id=video_source_id,
            source_type=source_type,
        )
        for keyword in positive_keywords:
            self.sqlite_adapter.add_search_keyword(conn, plan["id"], keyword, is_negative=False)
        for keyword in negative:
            self.sqlite_adapter.add_search_keyword(conn, plan["id"], keyword, is_negative=True)
        return self.get_plan(conn, plan["id"]) or plan

    def run_search(self, conn: sqlite3.Connection, *, plan_id: str) -> dict[str, Any] | None:
        plan = self.get_plan(conn, plan_id)
        if not plan:
            return None

        keywords_payload = self.sqlite_adapter.list_search_plan_keywords(conn, plan_id)
        positive_keywords = [item["keyword"] for item in keywords_payload if not item.get("is_negative")]
        negative_keywords = [item["keyword"] for item in keywords_payload if item.get("is_negative")]

        conn.execute(
            "UPDATE search_plans SET status = 'running', updated_at = ? WHERE id = ?",
            (self.sqlite_adapter.utc_now_iso(), plan_id),
        )

        rank = 1
        for keyword in positive_keywords or [plan["query"]]:
            query = f"{plan['query']} {keyword}".strip()
            for result in self.search_provider.search(query=query, keywords=[keyword]):
                if self._contains_any((result.get("title") or "") + " " + (result.get("channel_name") or ""), negative_keywords):
                    continue
                self.sqlite_adapter.add_search_result(
                    conn,
                    search_plan_id=plan_id,
                    source_video_id=result.get("source_video_id"),
                    title=result.get("title"),
                    source_url=result.get("source_url"),
                    channel_name=result.get("channel_name"),
                    relevance_score=result.get("relevance_score"),
                    ranking=result.get("ranking") or rank,
                    query_keyword=keyword,
                )
                rank += 1

        conn.execute(
            "UPDATE search_plans SET status = 'review_pending', updated_at = ? WHERE id = ?",
            (self.sqlite_adapter.utc_now_iso(), plan_id),
        )
        return self.get_plan(conn, plan_id)

    def review_result(
        self,
        conn: sqlite3.Connection,
        *,
        result_id: str,
        approved: bool,
        reason: str | None = None,
    ) -> dict[str, Any] | None:
        result = self.sqlite_adapter.get_search_result(conn, result_id)
        if not result:
            return None

        status = "approved" if approved else "rejected"
        updated = self.sqlite_adapter.update_search_result_status(
            conn,
            result_id=result_id,
            status=status,
            reason=reason,
        )
        if approved:
            plan = self.get_plan(conn, result["search_plan_id"])
            if plan and plan.get("video_source_id"):
                queued = self.video_queue_service.enqueue(
                    conn,
                    video_source_id=plan["video_source_id"],
                    title=result.get("title"),
                    source_url=result.get("source_url"),
                    source_video_id=result.get("source_video_id"),
                )
                self.sqlite_adapter.update_search_result_status(
                    conn,
                    result_id=result_id,
                    status="approved",
                    reason=reason,
                    ingested_video_id=queued["video"]["id"],
                )
                updated = self.sqlite_adapter.get_search_result(conn, result_id)

        self.sqlite_adapter.append_event(
            conn,
            event_type="search_result.reviewed",
            aggregate_type="search_result",
            aggregate_id=result_id,
            payload={"approved": approved, "reason": reason},
        )
        return updated

    def review_decision(
        self,
        conn: sqlite3.Connection,
        *,
        plan_id: str,
        approved: bool,
        reason: str | None = None,
    ) -> dict[str, Any] | None:
        next_status = "approved" if approved else "rejected"
        conn.execute(
            "UPDATE search_plans SET status = ?, review_reason = ?, updated_at = ? WHERE id = ?",
            (next_status, reason, self.sqlite_adapter.utc_now_iso(), plan_id),
        )
        if not approved:
            conn.execute(
                "UPDATE search_results SET status = 'rejected', review_reason = ?, updated_at = ? WHERE search_plan_id = ? AND status = 'pending'",
                (reason, self.sqlite_adapter.utc_now_iso(), plan_id),
            )
        return self.get_plan(conn, plan_id)

    def get_plan(self, conn: sqlite3.Connection, plan_id: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM search_plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            return None
        plan = dict(row)
        plan["keywords"] = self.sqlite_adapter.list_search_plan_keywords(conn, plan_id)
        plan["results"] = self.sqlite_adapter.list_search_results(conn, plan_id)
        return plan

    def _build_groq_planner(self, settings: Settings) -> GroqKeywordPlanner | None:
        if not settings.groq_plan_generation_enabled:
            return None
        if not settings.groq_api_key or not settings.groq_model:
            return None
        return GroqKeywordPlanner(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            base_url=settings.groq_base_url or "https://api.groq.com/openai/v1",
            timeout_seconds=settings.groq_timeout_seconds,
        )

    def _validate_safety(self, query: str, keywords: list[str]) -> None:
        text = f"{query} {' '.join(keywords)}"
        if self._contains_any(text, list(self._UNSAFE_TERMS)):
            raise ValueError("Unsafe query is not allowed for search plan generation.")

    @staticmethod
    def _contains_any(text: str, terms: list[str]) -> bool:
        lowered = text.lower()
        return any(re.search(rf"\\b{re.escape(term.lower())}\\b", lowered) for term in terms if term)
