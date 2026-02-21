from __future__ import annotations

from core.settings import get_settings
from dal.local.sqlite_adapter import LocalSQLiteAdapter
from domain.services.video_queue_service import VideoQueueService
from presentation.handlers.response_dto import PresentationResponseDTO


class VideoQueueHandler:
    def __init__(self) -> None:
        settings = get_settings()
        self.sqlite_adapter = LocalSQLiteAdapter(settings.db_path)
        self.service = VideoQueueService(self.sqlite_adapter)

    def list_videos(self) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            rows = conn.execute(
                """
                SELECT v.*, COALESCE(MAX(j.priority), 0) AS priority
                FROM videos v
                LEFT JOIN jobs j ON json_extract(j.payload_json, '$.video_id') = v.id
                GROUP BY v.id
                ORDER BY v.created_at DESC
                """
            ).fetchall()
            videos = [dict(row) for row in rows]
        return PresentationResponseDTO(status_code=200, message="Video queue fetched successfully.", data=videos)

    def update_priority(self, video_id: str, priority: int) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            job = conn.execute(
                "SELECT id FROM jobs WHERE json_extract(payload_json, '$.video_id') = ? ORDER BY created_at DESC LIMIT 1",
                (video_id,),
            ).fetchone()
            if not job:
                return PresentationResponseDTO(status_code=404, message="Video job not found.", data=None)
            updated = self.service.reprioritize(conn, job_id=job["id"], priority=priority)
        return PresentationResponseDTO(status_code=200, message="Video priority updated.", data=updated)

    def retry_video(self, video_id: str) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            video = self.service.retry(conn, video_id=video_id, reason="manual retry from UI")
        if not video:
            return PresentationResponseDTO(status_code=404, message="Video not found.", data=None)
        return PresentationResponseDTO(status_code=200, message="Video retry scheduled.", data=video)

    def disable_video(self, video_id: str) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            video = self.service.disable(conn, video_id=video_id)
        if not video:
            return PresentationResponseDTO(status_code=404, message="Video not found.", data=None)
        return PresentationResponseDTO(status_code=200, message="Video disabled.", data=video)

    def enable_video(self, video_id: str) -> PresentationResponseDTO:
        with self.sqlite_adapter.connect() as conn:
            self.sqlite_adapter.run_migrations(conn, "dal/local/migrations")
            video = self.service.enable(conn, video_id=video_id)
        if not video:
            return PresentationResponseDTO(status_code=404, message="Video not found.", data=None)
        return PresentationResponseDTO(status_code=200, message="Video enabled.", data=video)


_HANDLER = VideoQueueHandler()


def list_videos() -> PresentationResponseDTO:
    return _HANDLER.list_videos()


def update_priority(video_id: str, priority: int) -> PresentationResponseDTO:
    return _HANDLER.update_priority(video_id, priority)


def retry_video(video_id: str) -> PresentationResponseDTO:
    return _HANDLER.retry_video(video_id)


def disable_video(video_id: str) -> PresentationResponseDTO:
    return _HANDLER.disable_video(video_id)


def enable_video(video_id: str) -> PresentationResponseDTO:
    return _HANDLER.enable_video(video_id)
