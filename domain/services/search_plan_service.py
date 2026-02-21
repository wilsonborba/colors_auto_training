from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Protocol

from dal.local.sqlite_adapter import LocalSQLiteAdapter


class SearchProviderPort(Protocol):
    def search(self, *, query: str, keywords: list[str]) -> Iterable[dict[str, Any]]: ...


class SearchPlanService:
    """Creates plans, runs remote search, and applies review decisions."""

    def __init__(self, sqlite_adapter: LocalSQLiteAdapter, search_provider: SearchProviderPort) -> None:
        self.sqlite_adapter = sqlite_adapter
        self.search_provider = search_provider

    def create_plan(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        keywords: list[str] | None = None,
        video_source_id: str | None = None,
    ) -> dict[str, Any]:
        plan = self.sqlite_adapter.create_search_plan(conn, query=query, video_source_id=video_source_id)
        for keyword in keywords or []:
            self.sqlite_adapter.add_search_keyword(conn, plan["id"], keyword)
        return self.get_plan(conn, plan["id"]) or plan

    def run_search(self, conn: sqlite3.Connection, *, plan_id: str) -> dict[str, Any] | None:
        plan = self.get_plan(conn, plan_id)
        if not plan:
            return None

        keywords = [item["keyword"] for item in self._list_keywords(conn, plan_id)]
        conn.execute(
            "UPDATE search_plans SET status = 'running', updated_at = ? WHERE id = ?",
            (self.sqlite_adapter.utc_now_iso(), plan_id),
        )

        for rank, result in enumerate(self.search_provider.search(query=plan["query"], keywords=keywords), start=1):
            self.sqlite_adapter.add_search_result(
                conn,
                search_plan_id=plan_id,
                source_video_id=result.get("source_video_id"),
                title=result.get("title"),
                source_url=result.get("source_url"),
                channel_name=result.get("channel_name"),
                relevance_score=result.get("relevance_score"),
                ranking=result.get("ranking") or rank,
            )

        conn.execute(
            "UPDATE search_plans SET status = 'review_pending', updated_at = ? WHERE id = ?",
            (self.sqlite_adapter.utc_now_iso(), plan_id),
        )
        return self.get_plan(conn, plan_id)

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
            "UPDATE search_plans SET status = ?, updated_at = ? WHERE id = ?",
            (next_status, self.sqlite_adapter.utc_now_iso(), plan_id),
        )
        if reason:
            conn.execute(
                """
                UPDATE search_results
                SET status = CASE WHEN ? THEN 'approved' ELSE 'rejected' END,
                    updated_at = ?
                WHERE search_plan_id = ?
                """,
                (int(approved), self.sqlite_adapter.utc_now_iso(), plan_id),
            )
            self.sqlite_adapter.append_event(
                conn,
                event_type="search_plan.reviewed",
                aggregate_type="search_plan",
                aggregate_id=plan_id,
                payload={"approved": approved, "reason": reason},
            )
        return self.get_plan(conn, plan_id)

    def get_plan(self, conn: sqlite3.Connection, plan_id: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM search_plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            return None
        plan = dict(row)
        plan["keywords"] = self._list_keywords(conn, plan_id)
        plan["results"] = self.sqlite_adapter.list_search_results(conn, plan_id)
        return plan

    def _list_keywords(self, conn: sqlite3.Connection, plan_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM search_plan_keywords WHERE search_plan_id = ? ORDER BY created_at ASC",
            (plan_id,),
        ).fetchall()
        return [dict(item) for item in rows]
