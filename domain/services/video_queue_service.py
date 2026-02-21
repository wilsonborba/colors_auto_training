from __future__ import annotations

import sqlite3
from typing import Any

from dal.local.sqlite_adapter import LocalSQLiteAdapter


class VideoQueueService:
    """Service for queueing and mutating video processing state."""

    def __init__(self, sqlite_adapter: LocalSQLiteAdapter) -> None:
        self.sqlite_adapter = sqlite_adapter

    def enqueue(
        self,
        conn: sqlite3.Connection,
        *,
        video_source_id: str,
        title: str | None,
        source_url: str | None,
        source_video_id: str | None = None,
        priority: int = 0,
    ) -> dict[str, Any]:
        video = self.sqlite_adapter.create_video(
            conn,
            video_source_id=video_source_id,
            title=title,
            source_url=source_url,
            local_path=None,
            file_size_bytes=None,
            sha256=None,
        )
        if source_video_id:
            conn.execute(
                """
                UPDATE videos
                SET source_video_id = COALESCE(source_video_id, ?), updated_at = ?
                WHERE id = ?
                """,
                (source_video_id, self.sqlite_adapter.utc_now_iso(), video["id"]),
            )
            video = self._get_video(conn, video["id"]) or video

        job = self.sqlite_adapter.create_job(
            conn,
            job_type="download_video",
            payload={
                "video_id": video["id"],
                "video_source_id": video["video_source_id"],
                "source_video_id": video.get("source_video_id"),
                "source_url": video.get("source_url"),
            },
            priority=priority,
        )
        return {"video": video, "job": job}

    def reprioritize(self, conn: sqlite3.Connection, *, job_id: str, priority: int) -> dict[str, Any] | None:
        now = self.sqlite_adapter.utc_now_iso()
        conn.execute("UPDATE jobs SET priority = ?, updated_at = ? WHERE id = ?", (priority, now, job_id))
        return self.sqlite_adapter.get_job(conn, job_id)

    def retry(self, conn: sqlite3.Connection, *, video_id: str, reason: str | None = None) -> dict[str, Any] | None:
        now = self.sqlite_adapter.utc_now_iso()
        conn.execute(
            """
            UPDATE videos
            SET retries = retries + 1,
                status = 'queued',
                updated_at = ?
            WHERE id = ?
            """,
            (now, video_id),
        )
        conn.execute(
            """
            UPDATE jobs
            SET status = 'queued',
                last_error = ?,
                run_after_at = NULL,
                locked_by = NULL,
                locked_at = NULL,
                updated_at = ?
            WHERE json_extract(payload_json, '$.video_id') = ?
            """,
            (reason, now, video_id),
        )
        return self._get_video(conn, video_id)

    def disable(self, conn: sqlite3.Connection, *, video_id: str) -> dict[str, Any] | None:
        now = self.sqlite_adapter.utc_now_iso()
        conn.execute("UPDATE videos SET is_enabled = 0, updated_at = ? WHERE id = ?", (now, video_id))
        return self._get_video(conn, video_id)

    def enable(self, conn: sqlite3.Connection, *, video_id: str) -> dict[str, Any] | None:
        now = self.sqlite_adapter.utc_now_iso()
        conn.execute("UPDATE videos SET is_enabled = 1, updated_at = ? WHERE id = ?", (now, video_id))
        return self._get_video(conn, video_id)

    def _get_video(self, conn: sqlite3.Connection, video_id: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
        return dict(row) if row else None
