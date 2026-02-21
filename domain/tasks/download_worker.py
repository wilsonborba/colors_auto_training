from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Callable

from dal.local.sqlite_adapter import LocalSQLiteAdapter
from domain.services.download_service import DownloadError, DownloadService
from domain.services.event_service import EventService


class DownloadWorker:
    """Periodic worker that transactionally claims queued jobs and processes downloads."""

    def __init__(
        self,
        sqlite_adapter: LocalSQLiteAdapter,
        download_service: DownloadService,
        event_service: EventService,
        *,
        worker_id: str,
        base_backoff_seconds: int = 10,
        max_backoff_seconds: int = 1800,
    ) -> None:
        self.sqlite_adapter = sqlite_adapter
        self.download_service = download_service
        self.event_service = event_service
        self.worker_id = worker_id
        self.base_backoff_seconds = base_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds

    def run_loop(
        self,
        conn: sqlite3.Connection,
        *,
        poll_interval_seconds: float = 1.0,
        stop_when_idle: bool = False,
        on_progress: Callable[[dict[str, Any]], None] | None = None,
    ) -> int:
        processed = 0
        while True:
            job = self.sqlite_adapter.claim_next_job(conn, worker_id=self.worker_id)
            if not job:
                if stop_when_idle:
                    return processed
                time.sleep(poll_interval_seconds)
                continue

            processed += 1
            self._process_job(conn, job, on_progress=on_progress)

    def _process_job(
        self,
        conn: sqlite3.Connection,
        job: dict[str, Any],
        *,
        on_progress: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        payload = json.loads(job.get("payload_json") or "{}")
        if job["job_type"] != "download_video":
            self.sqlite_adapter.update_job_status(conn, job["id"], "failed", last_error="unsupported_job_type")
            return

        video_id = payload.get("video_id")
        source_url = payload.get("source_url")
        video_source_id = payload.get("video_source_id")
        source_video_id = payload.get("source_video_id")
        title = payload.get("title")

        if not source_url or not video_source_id or not video_id:
            self.sqlite_adapter.update_job_status(conn, job["id"], "failed", last_error="invalid_payload")
            return

        self.event_service.append_event(
            conn,
            event_type="job.started",
            aggregate_type="job",
            aggregate_id=job["id"],
            payload={"job_type": job["job_type"], "video_id": video_id},
        )

        def _progress(progress: dict[str, Any]) -> None:
            self.event_service.append_event(
                conn,
                event_type="download.progress",
                aggregate_type="job",
                aggregate_id=job["id"],
                payload={"video_id": video_id, **progress},
            )
            if on_progress:
                on_progress(progress)

        try:
            result = self.download_service.execute_download(
                conn,
                worker_id=self.worker_id,
                video_source_id=video_source_id,
                source_url=source_url,
                source_video_id=source_video_id,
                title=title,
                progress_callback=_progress,
            )
            now = self.sqlite_adapter.utc_now_iso()
            conn.execute(
                "UPDATE videos SET status = 'downloaded', updated_at = ? WHERE id = ?",
                (now, result.video["id"]),
            )
            self.sqlite_adapter.update_job_status(conn, job["id"], "completed")
            self.event_service.append_event(
                conn,
                event_type="job.completed",
                aggregate_type="job",
                aggregate_id=job["id"],
                payload={"video_id": result.video["id"], "claimed": result.claimed},
            )
        except DownloadError as exc:
            self._apply_retry(conn, job, video_id=video_id, reason_code=exc.code, message=exc.message)

    def _apply_retry(
        self,
        conn: sqlite3.Connection,
        job: dict[str, Any],
        *,
        video_id: str,
        reason_code: str,
        message: str,
    ) -> None:
        attempts = int(job["attempts"])
        max_attempts = int(job["max_attempts"])
        now = self.sqlite_adapter.utc_now_iso()

        conn.execute(
            "UPDATE videos SET status = 'failed', retries = retries + 1, updated_at = ? WHERE id = ?",
            (now, video_id),
        )
        self.event_service.append_event(
            conn,
            event_type="job.failed",
            aggregate_type="job",
            aggregate_id=job["id"],
            payload={"reason_code": reason_code, "message": message, "attempts": attempts, "max_attempts": max_attempts},
        )

        if attempts >= max_attempts:
            self.sqlite_adapter.update_job_status(
                conn,
                job["id"],
                "failed",
                last_error=f"{reason_code}:{message}",
            )
            return

        backoff_seconds = min(self.max_backoff_seconds, self.base_backoff_seconds * (2 ** (attempts - 1)))
        run_after = conn.execute("SELECT datetime('now', ?) AS run_after", (f"+{backoff_seconds} seconds",)).fetchone()["run_after"]

        conn.execute(
            """
            UPDATE jobs
            SET status = 'queued',
                last_error = ?,
                run_after_at = ?,
                locked_by = NULL,
                locked_at = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (f"{reason_code}:{message}", run_after, now, job["id"]),
        )
        self.event_service.append_event(
            conn,
            event_type="job.retry_scheduled",
            aggregate_type="job",
            aggregate_id=job["id"],
            payload={"reason_code": reason_code, "run_after_at": run_after, "backoff_seconds": backoff_seconds},
        )
