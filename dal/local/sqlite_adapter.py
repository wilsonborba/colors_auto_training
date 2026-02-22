from __future__ import annotations

import contextlib
import datetime as dt
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterator


class LocalSQLiteAdapter:
    """SQLite adapter with migration support and transactional helpers."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        busy_timeout_ms: int = 5000,
    ) -> None:
        self.db_path = Path(db_path)
        self.busy_timeout_ms = busy_timeout_ms
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def utc_now_iso() -> str:
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms};")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def run_migrations(self, conn: sqlite3.Connection, migrations_dir: str | Path) -> None:
        migrations_path = Path(migrations_dir)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        applied = {
            row["version"]
            for row in conn.execute("SELECT version FROM schema_migrations")
        }

        for migration in sorted(migrations_path.glob("*.sql")):
            version = migration.name
            if version in applied:
                continue
            sql = migration.read_text(encoding="utf-8")
            conn.executescript("BEGIN;\n" + sql + "\nCOMMIT;")
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (version, self.utc_now_iso()),
            )

    @contextlib.contextmanager
    def transaction(self, conn: sqlite3.Connection, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        try:
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    # --- Video sources ---
    def create_video_source(self, conn: sqlite3.Connection, source_type: str, display_name: str | None = None) -> dict[str, Any]:
        source_id = str(uuid.uuid4())
        now = self.utc_now_iso()
        conn.execute(
            """
            INSERT INTO video_sources(id, source_type, display_name, is_enabled, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (source_id, source_type, display_name, now, now),
        )
        return self.get_video_source(conn, source_id)

    def get_video_source(self, conn: sqlite3.Connection, source_id: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM video_sources WHERE id = ?", (source_id,)).fetchone()
        return dict(row) if row else None

    # --- Videos + idempotency helpers ---
    def find_video_by_sha256(self, conn: sqlite3.Connection, sha256: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM videos WHERE sha256 = ?", (sha256,)).fetchone()
        return dict(row) if row else None

    def find_video_by_path_and_size(self, conn: sqlite3.Connection, local_path: str, file_size_bytes: int) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM videos WHERE local_path = ? AND file_size_bytes = ?",
            (local_path, file_size_bytes),
        ).fetchone()
        return dict(row) if row else None

    def create_video(
        self,
        conn: sqlite3.Connection,
        *,
        video_source_id: str,
        title: str | None,
        source_url: str | None,
        local_path: str | None,
        file_size_bytes: int | None,
        sha256: str | None,
    ) -> dict[str, Any]:
        existing = None
        if sha256:
            existing = self.find_video_by_sha256(conn, sha256)
        if not existing and local_path is not None and file_size_bytes is not None:
            existing = self.find_video_by_path_and_size(conn, local_path, file_size_bytes)
        if existing:
            return existing

        video_id = str(uuid.uuid4())
        now = self.utc_now_iso()
        conn.execute(
            """
            INSERT INTO videos(
                id, video_source_id, title, source_url, local_path, file_size_bytes, sha256,
                status, is_enabled, retries, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 1, 0, ?, ?)
            """,
            (video_id, video_source_id, title, source_url, local_path, file_size_bytes, sha256, now, now),
        )
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
        return dict(row)

    # --- Download registry to avoid duplicate downloads ---
    def find_download_by_source_video_id(
        self,
        conn: sqlite3.Connection,
        video_source_id: str,
        source_video_id: str,
    ) -> dict[str, Any] | None:
        row = conn.execute(
            """
            SELECT *
            FROM video_downloads
            WHERE video_source_id = ? AND source_video_id = ?
            """,
            (video_source_id, source_video_id),
        ).fetchone()
        return dict(row) if row else None

    def find_download_by_sha256(self, conn: sqlite3.Connection, sha256: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM video_downloads WHERE sha256 = ?", (sha256,)).fetchone()
        return dict(row) if row else None

    def find_download_by_path_and_size(
        self,
        conn: sqlite3.Connection,
        local_path: str,
        file_size_bytes: int,
    ) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT * FROM video_downloads WHERE local_path = ? AND file_size_bytes = ?",
            (local_path, file_size_bytes),
        ).fetchone()
        return dict(row) if row else None

    def claim_video_download(
        self,
        conn: sqlite3.Connection,
        *,
        video_source_id: str,
        claimed_by: str,
        source_video_id: str | None = None,
        source_url: str | None = None,
        local_path: str | None = None,
        file_size_bytes: int | None = None,
        sha256: str | None = None,
    ) -> tuple[dict[str, Any], bool]:
        now = self.utc_now_iso()
        with self.transaction(conn, immediate=True):
            existing = None
            if source_video_id:
                existing = self.find_download_by_source_video_id(conn, video_source_id, source_video_id)
            if not existing and sha256:
                existing = self.find_download_by_sha256(conn, sha256)
            if not existing and local_path is not None and file_size_bytes is not None:
                existing = self.find_download_by_path_and_size(conn, local_path, file_size_bytes)

            if existing:
                if existing["status"] in {"downloading", "downloaded"}:
                    return existing, False

                conn.execute(
                    """
                    UPDATE video_downloads
                    SET status = 'downloading',
                        claimed_by = ?,
                        claimed_at = ?,
                        source_url = COALESCE(?, source_url),
                        local_path = COALESCE(?, local_path),
                        file_size_bytes = COALESCE(?, file_size_bytes),
                        sha256 = COALESCE(?, sha256),
                        last_error = NULL,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (claimed_by, now, source_url, local_path, file_size_bytes, sha256, now, existing["id"]),
                )
                updated = conn.execute("SELECT * FROM video_downloads WHERE id = ?", (existing["id"],)).fetchone()
                return dict(updated), True

            download_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO video_downloads(
                    id, video_source_id, source_video_id, source_url, local_path, file_size_bytes,
                    sha256, status, claimed_by, claimed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'downloading', ?, ?, ?, ?)
                """,
                (
                    download_id,
                    video_source_id,
                    source_video_id,
                    source_url,
                    local_path,
                    file_size_bytes,
                    sha256,
                    claimed_by,
                    now,
                    now,
                    now,
                ),
            )
            created = conn.execute("SELECT * FROM video_downloads WHERE id = ?", (download_id,)).fetchone()
            return dict(created), True

    def mark_video_downloaded(
        self,
        conn: sqlite3.Connection,
        download_id: str,
        *,
        downloaded_video_id: str | None,
        sha256: str | None = None,
        local_path: str | None = None,
        file_size_bytes: int | None = None,
    ) -> dict[str, Any] | None:
        now = self.utc_now_iso()
        conn.execute(
            """
            UPDATE video_downloads
            SET status = 'downloaded',
                downloaded_video_id = ?,
                downloaded_at = ?,
                sha256 = COALESCE(?, sha256),
                local_path = COALESCE(?, local_path),
                file_size_bytes = COALESCE(?, file_size_bytes),
                last_error = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (downloaded_video_id, now, sha256, local_path, file_size_bytes, now, download_id),
        )
        row = conn.execute("SELECT * FROM video_downloads WHERE id = ?", (download_id,)).fetchone()
        return dict(row) if row else None

    def mark_video_download_failed(self, conn: sqlite3.Connection, download_id: str, error_message: str) -> dict[str, Any] | None:
        now = self.utc_now_iso()
        conn.execute(
            """
            UPDATE video_downloads
            SET status = 'failed',
                last_error = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (error_message, now, download_id),
        )
        row = conn.execute("SELECT * FROM video_downloads WHERE id = ?", (download_id,)).fetchone()
        return dict(row) if row else None

    def is_video_already_downloaded(
        self,
        conn: sqlite3.Connection,
        *,
        video_source_id: str,
        source_video_id: str | None = None,
        sha256: str | None = None,
        local_path: str | None = None,
        file_size_bytes: int | None = None,
    ) -> bool:
        record = None
        if source_video_id:
            record = self.find_download_by_source_video_id(conn, video_source_id, source_video_id)
        if not record and sha256:
            record = self.find_download_by_sha256(conn, sha256)
        if not record and local_path is not None and file_size_bytes is not None:
            record = self.find_download_by_path_and_size(conn, local_path, file_size_bytes)
        return bool(record and record["status"] == "downloaded")

    # --- Jobs with concurrency-safe claiming ---
    def create_job(
        self,
        conn: sqlite3.Connection,
        *,
        job_type: str,
        payload: dict[str, Any] | None,
        priority: int = 0,
        run_after_at: str | None = None,
    ) -> dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = self.utc_now_iso()
        conn.execute(
            """
            INSERT INTO jobs(
                id, job_type, status, payload_json, priority, run_after_at, attempts,
                max_attempts, created_at, updated_at
            ) VALUES (?, ?, 'queued', ?, ?, ?, 0, 3, ?, ?)
            """,
            (job_id, job_type, json.dumps(payload or {}), priority, run_after_at, now, now),
        )
        return self.get_job(conn, job_id)

    def get_job(self, conn: sqlite3.Connection, job_id: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None

    def claim_next_job(self, conn: sqlite3.Connection, worker_id: str, now_iso: str | None = None) -> dict[str, Any] | None:
        now = now_iso or self.utc_now_iso()
        with self.transaction(conn, immediate=True):
            candidate = conn.execute(
                """
                SELECT id
                FROM jobs
                WHERE status = 'queued'
                  AND (run_after_at IS NULL OR run_after_at <= ?)
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                """,
                (now,),
            ).fetchone()
            if not candidate:
                return None

            result = conn.execute(
                """
                UPDATE jobs
                SET status = 'running', locked_by = ?, locked_at = ?, attempts = attempts + 1, updated_at = ?
                WHERE id = ? AND status = 'queued'
                """,
                (worker_id, now, now, candidate["id"]),
            )
            if result.rowcount != 1:
                return None

            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (candidate["id"],)).fetchone()
            return dict(row) if row else None

    def update_job_status(
        self,
        conn: sqlite3.Connection,
        job_id: str,
        status: str,
        *,
        last_error: str | None = None,
        clear_lock: bool = True,
    ) -> dict[str, Any] | None:
        now = self.utc_now_iso()
        conn.execute(
            """
            UPDATE jobs
            SET status = ?, last_error = ?,
                locked_by = CASE WHEN ? THEN NULL ELSE locked_by END,
                locked_at = CASE WHEN ? THEN NULL ELSE locked_at END,
                updated_at = ?
            WHERE id = ?
            """,
            (status, last_error, int(clear_lock), int(clear_lock), now, job_id),
        )
        return self.get_job(conn, job_id)

    # --- Search plans and results ---
    def create_search_plan(
        self,
        conn: sqlite3.Connection,
        query: str,
        video_source_id: str | None = None,
        source_type: str = 'manual',
    ) -> dict[str, Any]:
        plan_id = str(uuid.uuid4())
        now = self.utc_now_iso()
        conn.execute(
            """
            INSERT INTO search_plans(id, video_source_id, query, source_type, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'draft', ?, ?)
            """,
            (plan_id, video_source_id, query, source_type, now, now),
        )
        row = conn.execute("SELECT * FROM search_plans WHERE id = ?", (plan_id,)).fetchone()
        return dict(row)

    def add_search_keyword(
        self,
        conn: sqlite3.Connection,
        search_plan_id: str,
        keyword: str,
        weight: float = 1.0,
        is_negative: bool = False,
    ) -> dict[str, Any]:
        keyword_id = str(uuid.uuid4())
        now = self.utc_now_iso()
        conn.execute(
            """
            INSERT INTO search_plan_keywords(id, search_plan_id, keyword, weight, is_negative, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (keyword_id, search_plan_id, keyword, weight, int(is_negative), now),
        )
        row = conn.execute("SELECT * FROM search_plan_keywords WHERE id = ?", (keyword_id,)).fetchone()
        return dict(row)

    def add_search_result(
        self,
        conn: sqlite3.Connection,
        *,
        search_plan_id: str,
        source_video_id: str | None,
        title: str | None,
        source_url: str | None,
        channel_name: str | None,
        relevance_score: float | None,
        ranking: int | None,
        query_keyword: str | None = None,
    ) -> dict[str, Any]:
        result_id = str(uuid.uuid4())
        now = self.utc_now_iso()
        conn.execute(
            """
            INSERT INTO search_results(
                id, search_plan_id, source_video_id, title, source_url, channel_name,
                relevance_score, ranking, query_keyword, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (result_id, search_plan_id, source_video_id, title, source_url, channel_name, relevance_score, ranking, query_keyword, now, now),
        )
        row = conn.execute("SELECT * FROM search_results WHERE id = ?", (result_id,)).fetchone()
        return dict(row)

    def list_search_results(self, conn: sqlite3.Connection, search_plan_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM search_results WHERE search_plan_id = ? ORDER BY ranking ASC, created_at ASC",
            (search_plan_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def update_search_result_status(
        self,
        conn: sqlite3.Connection,
        *,
        result_id: str,
        status: str,
        reason: str | None = None,
        ingested_video_id: str | None = None,
    ) -> dict[str, Any] | None:
        now = self.utc_now_iso()
        conn.execute(
            "UPDATE search_results SET status = ?, review_reason = ?, ingested_video_id = COALESCE(?, ingested_video_id), updated_at = ? WHERE id = ?",
            (status, reason, ingested_video_id, now, result_id),
        )
        row = conn.execute("SELECT * FROM search_results WHERE id = ?", (result_id,)).fetchone()
        return dict(row) if row else None

    def list_search_plan_keywords(self, conn: sqlite3.Connection, search_plan_id: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM search_plan_keywords WHERE search_plan_id = ? ORDER BY created_at ASC",
            (search_plan_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_search_result(self, conn: sqlite3.Connection, result_id: str) -> dict[str, Any] | None:
        row = conn.execute("SELECT * FROM search_results WHERE id = ?", (result_id,)).fetchone()
        return dict(row) if row else None
    # --- Events (optional) ---
    def append_event(
        self,
        conn: sqlite3.Connection,
        *,
        event_type: str,
        payload: dict[str, Any],
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> dict[str, Any]:
        event_id = str(uuid.uuid4())
        now = self.utc_now_iso()
        conn.execute(
            """
            INSERT INTO events(id, event_type, aggregate_type, aggregate_id, entity_type, entity_id, payload_json, created_at, ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_type,
                aggregate_type,
                aggregate_id,
                entity_type or aggregate_type,
                entity_id or aggregate_id,
                json.dumps(payload),
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return dict(row)

    def tail_events(self, conn: sqlite3.Connection, limit: int = 100) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def tail_events_by_entity(self, conn: sqlite3.Connection, *, entity_type: str, entity_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM events WHERE entity_type = ? AND entity_id = ? ORDER BY ts DESC LIMIT ?",
            (entity_type, entity_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
