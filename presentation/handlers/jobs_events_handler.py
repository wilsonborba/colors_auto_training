from __future__ import annotations

import json

from core.settings import get_settings
from dal.local.sqlite_adapter import LocalSQLiteAdapter
from presentation.handlers.response_dto import PresentationResponseDTO


class JobsEventsHandler:
    def __init__(self) -> None:
        settings = get_settings()
        self.sqlite_adapter = LocalSQLiteAdapter(settings.db_path)

    def get_active_jobs(self) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            rows = conn.execute(
                """
                SELECT id, job_type, status, priority, attempts, max_attempts, last_error, created_at, updated_at
                FROM jobs
                WHERE status IN ('queued', 'running')
                ORDER BY priority DESC, created_at ASC
                """
            ).fetchall()
            jobs = [dict(row) for row in rows]
        return PresentationResponseDTO(status_code=200, message="Active jobs fetched successfully.", data=jobs)

    def tail_events(self, limit: int) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            rows = self.sqlite_adapter.tail_events(conn, limit=limit)
            events = []
            for row in rows:
                payload = row.get("payload_json")
                events.append({**row, "payload": json.loads(payload) if payload else {}})
        return PresentationResponseDTO(status_code=200, message="Event tail fetched successfully.", data=events)


_HANDLER = JobsEventsHandler()


def get_active_jobs() -> PresentationResponseDTO:
    return _HANDLER.get_active_jobs()


def tail_events(limit: int) -> PresentationResponseDTO:
    return _HANDLER.tail_events(limit)
