from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from dal.local.sqlite_adapter import LocalSQLiteAdapter


class DownloadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class RemoteDownloadNotFoundError(Exception):
    pass


class RemoteDownloadRateLimitedError(Exception):
    pass


class RemoteDownloadTemporaryError(Exception):
    pass


class DownloaderPort(Protocol):
    def download(
        self,
        *,
        source_url: str,
        source_video_id: str | None,
        destination_dir: Path,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> Path: ...


@dataclass(slots=True)
class DownloadResult:
    download: dict[str, Any]
    video: dict[str, Any]
    claimed: bool


class DownloadService:
    """Coordinates idempotent download claims and persistence updates."""

    def __init__(self, sqlite_adapter: LocalSQLiteAdapter, downloader: DownloaderPort, download_dir: Path | str) -> None:
        self.sqlite_adapter = sqlite_adapter
        self.downloader = downloader
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def execute_download(
        self,
        conn: sqlite3.Connection,
        *,
        worker_id: str,
        video_source_id: str,
        source_url: str,
        source_video_id: str | None = None,
        title: str | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> DownloadResult:
        if self.sqlite_adapter.is_video_already_downloaded(
            conn,
            video_source_id=video_source_id,
            source_video_id=source_video_id,
        ):
            existing = self.sqlite_adapter.find_download_by_source_video_id(conn, video_source_id, source_video_id or "")
            if not existing:
                raise DownloadError("idempotency_lookup_failed", "Video marked downloaded but registry row was not found.")
            video = self.sqlite_adapter.get_video(conn, existing["downloaded_video_id"])
            if not video:
                raise DownloadError("idempotency_lookup_failed", "Download registry references a missing video.")
            return DownloadResult(download=existing, video=video, claimed=False)

        download, claimed = self.sqlite_adapter.claim_video_download(
            conn,
            video_source_id=video_source_id,
            source_video_id=source_video_id,
            source_url=source_url,
            claimed_by=worker_id,
        )
        if not claimed and download.get("downloaded_video_id"):
            existing = self.sqlite_adapter.get_video(conn, download["downloaded_video_id"])
            if not existing:
                raise DownloadError("idempotency_lookup_failed", "Download was completed but no video row exists.")
            return DownloadResult(download=download, video=existing, claimed=False)

        try:
            downloaded_path = self.downloader.download(
                source_url=source_url,
                source_video_id=source_video_id,
                destination_dir=self.download_dir,
                progress_callback=progress_callback,
            )
        except Exception as exc:  # map adapter errors into domain reason codes
            mapped = self._map_download_error(exc)
            self.sqlite_adapter.mark_video_download_failed(conn, download["id"], mapped.message)
            raise mapped from exc

        if not downloaded_path.exists():
            self.sqlite_adapter.mark_video_download_failed(conn, download["id"], "Downloader returned a missing file path.")
            raise DownloadError("file_missing", "Downloader returned a missing file path.")

        file_size_bytes = downloaded_path.stat().st_size
        sha256 = self._sha256(downloaded_path)

        video = self.sqlite_adapter.create_video(
            conn,
            video_source_id=video_source_id,
            title=title,
            source_url=source_url,
            local_path=str(downloaded_path),
            file_size_bytes=file_size_bytes,
            sha256=sha256,
        )
        self.sqlite_adapter.mark_video_downloaded(
            conn,
            download["id"],
            downloaded_video_id=video["id"],
            sha256=sha256,
            local_path=str(downloaded_path),
            file_size_bytes=file_size_bytes,
        )
        return DownloadResult(download=download, video=video, claimed=claimed)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_obj:
            for block in iter(lambda: file_obj.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _map_download_error(exc: Exception) -> DownloadError:
        if isinstance(exc, RemoteDownloadNotFoundError):
            return DownloadError("source_not_found", str(exc) or "Source video could not be found.")
        if isinstance(exc, RemoteDownloadRateLimitedError):
            return DownloadError("rate_limited", str(exc) or "Download was rate limited.")
        if isinstance(exc, RemoteDownloadTemporaryError):
            return DownloadError("temporary_remote_error", str(exc) or "Temporary remote download error.")
        return DownloadError("unexpected_download_error", str(exc) or "Unexpected download error.")
