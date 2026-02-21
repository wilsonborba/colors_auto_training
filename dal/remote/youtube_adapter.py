"""
YouTube adapter (DAL - remote)

Responsibilities:
- Search videos by keywords (if enabled)
- Fetch metadata (title, channel, duration, etc.)
- Download video / audio streams (implementation choice)
- Report progress callbacks to caller
- Raise typed adapter errors (no HTTP status codes here)

This file must not:
- Decide job priorities
- Update UI state directly
- Orchestrate pipeline stages
Those belong to domain services/tasks.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from core.settings import get_settings


class YouTubeAdapterError(Exception):
    """Base adapter error that exposes retryability for callers."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable


class RetryableYouTubeAdapterError(YouTubeAdapterError):
    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=True)


class NonRetryableYouTubeAdapterError(YouTubeAdapterError):
    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=False)


class YouTubeNotFoundError(NonRetryableYouTubeAdapterError):
    pass


class YouTubeRateLimitedError(RetryableYouTubeAdapterError):
    pass


class YouTubeConfigurationError(NonRetryableYouTubeAdapterError):
    pass


class YouTubeDependencyError(NonRetryableYouTubeAdapterError):
    pass


ProgressCallback = Callable[[dict[str, Any]], None]


def get_youtube_adapter_config() -> dict[str, object | None]:
    """Return YouTube adapter configuration from centralized settings."""
    settings = get_settings()
    return {
        "enabled": settings.youtube_adapter_enabled,
        "api_key": settings.youtube_api_key,
        "base_url": settings.youtube_base_url,
        "timeout_seconds": settings.youtube_timeout_seconds,
    }


class YouTubeRemoteAdapter:
    """Remote-only YouTube operations without domain orchestration concerns."""

    def __init__(
        self,
        *,
        yt_dlp_bin: str = "yt-dlp",
    ) -> None:
        settings = get_settings()
        self.enabled = settings.youtube_adapter_enabled
        self.timeout_seconds = settings.youtube_timeout_seconds
        self.yt_dlp_bin = yt_dlp_bin

    def search_by_keywords(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        """Search by keywords via yt-dlp search extractor and normalize records."""
        cleaned = query.strip()
        if not cleaned:
            return []
        if not self.enabled:
            raise YouTubeConfigurationError("YouTube adapter is disabled by configuration.")
        if shutil.which(self.yt_dlp_bin) is None:
            raise YouTubeDependencyError(f"'{self.yt_dlp_bin}' was not found in PATH.")

        bounded_limit = max(1, min(limit, 50))
        command = [
            self.yt_dlp_bin,
            "--flat-playlist",
            "--dump-single-json",
            f"ytsearch{bounded_limit}:{cleaned}",
        ]
        result = _run_command(command)

        try:
            payload = json.loads(result)
        except json.JSONDecodeError as exc:
            raise RetryableYouTubeAdapterError("Search returned non-JSON data.") from exc

        records: list[dict[str, Any]] = []
        for entry in payload.get("entries", []) or []:
            if not isinstance(entry, dict):
                continue
            video_id = str(entry.get("id") or "").strip()
            if not video_id:
                continue
            records.append(
                {
                    "source": "youtube",
                    "source_video_id": video_id,
                    "source_url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": entry.get("title"),
                    "channel_title": entry.get("channel") or entry.get("uploader"),
                    "description": entry.get("description"),
                    "published_at": entry.get("upload_date"),
                    "thumbnail_url": entry.get("thumbnail"),
                }
            )
        return records

    def get_video_metadata(self, video_ref: str) -> dict[str, Any]:
        """Fetch normalized metadata for a YouTube video URL or plain video id via pytubefix."""
        if not self.enabled:
            raise YouTubeConfigurationError("YouTube adapter is disabled by configuration.")

        youtube_cls = _import_pytubefix_youtube()
        video_id = _extract_video_id(video_ref)
        source_url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            video = youtube_cls(source_url)
            vid_info = video.vid_info or {}
            details = (vid_info.get("videoDetails") or {}) if isinstance(vid_info, dict) else {}
        except Exception as exc:
            raise _map_runtime_error(exc) from exc

        if not details:
            raise YouTubeNotFoundError(f"Video metadata not found for '{video_ref}'.")

        thumbs = details.get("thumbnail") or {}
        thumb_list = thumbs.get("thumbnails") if isinstance(thumbs, dict) else None
        thumbnail_url = None
        if isinstance(thumb_list, list) and thumb_list:
            last = thumb_list[-1]
            if isinstance(last, dict):
                thumbnail_url = last.get("url")

        return {
            "source": "youtube",
            "source_video_id": video_id,
            "source_url": source_url,
            "title": details.get("title"),
            "channel_title": details.get("author"),
            "description": details.get("shortDescription"),
            "published_at": None,
            "duration": details.get("lengthSeconds"),
            "thumbnail_url": thumbnail_url,
            "view_count": _to_int(details.get("viewCount")),
            "like_count": None,
            "comment_count": None,
        }

    def download(
        self,
        *,
        source_url: str,
        destination_dir: Path,
        source_video_id: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> Path:
        """Download using pytubefix and emit progress callback percent/speed/eta when available."""
        if not self.enabled:
            raise YouTubeConfigurationError("YouTube adapter is disabled by configuration.")

        youtube_cls = _import_pytubefix_youtube()
        destination_dir.mkdir(parents=True, exist_ok=True)

        video_id = source_video_id or _extract_video_id(source_url)
        url = source_url if source_url.strip() else f"https://www.youtube.com/watch?v={video_id}"

        def _on_progress(_stream: Any, _chunk: bytes, bytes_remaining: int) -> None:
            total_bytes = getattr(_stream, "filesize", None) or getattr(_stream, "filesize_approx", None)
            if total_bytes is None:
                return

            downloaded = max(0, int(total_bytes) - int(bytes_remaining))
            percent = (downloaded / int(total_bytes)) * 100 if int(total_bytes) > 0 else 0.0
            payload: dict[str, Any] = {"percent": percent}

            if progress_callback:
                progress_callback(payload)

        try:
            yt = youtube_cls(url, on_progress_callback=_on_progress if progress_callback else None)
            stream = yt.streams.get_highest_resolution()
            if stream is None:
                raise YouTubeNotFoundError("No downloadable stream was found for this video.")
            output_name = f"{video_id}.{stream.subtype}"
            path_str = stream.download(output_path=str(destination_dir), filename=output_name)
            return Path(path_str)
        except YouTubeAdapterError:
            raise
        except Exception as exc:
            raise _map_runtime_error(exc) from exc


def _import_pytubefix_youtube() -> Any:
    try:
        from pytubefix import YouTube
    except ImportError as exc:
        raise YouTubeDependencyError("'pytubefix' is required for YouTube download/metadata operations.") from exc
    return YouTube


def _run_command(command: list[str]) -> str:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise RetryableYouTubeAdapterError(f"Failed to run command: {exc}") from exc

    if proc.returncode == 0:
        return proc.stdout

    message = (proc.stderr or proc.stdout or "command failed").strip()
    lowered = message.lower()
    if "429" in lowered or "rate" in lowered or "too many requests" in lowered:
        raise YouTubeRateLimitedError(message)
    if "not found" in lowered or "unavailable" in lowered:
        raise YouTubeNotFoundError(message)
    raise RetryableYouTubeAdapterError(message)


def _map_runtime_error(exc: Exception) -> YouTubeAdapterError:
    message = str(exc) or exc.__class__.__name__
    lowered = message.lower()
    if "404" in lowered or "not found" in lowered or "unavailable" in lowered:
        return YouTubeNotFoundError(message)
    if "429" in lowered or "too many requests" in lowered or "rate" in lowered:
        return YouTubeRateLimitedError(message)
    if "timeout" in lowered or "tempor" in lowered or "connection" in lowered:
        return RetryableYouTubeAdapterError(message)
    return NonRetryableYouTubeAdapterError(message)


def _extract_video_id(video_ref: str) -> str:
    candidate = video_ref.strip()
    if not candidate:
        raise YouTubeNotFoundError("Video reference must not be empty.")
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        return candidate

    parsed = urlparse(candidate)
    if parsed.netloc.endswith("youtu.be"):
        video_id = parsed.path.strip("/")
    else:
        params = parse_qs(parsed.query)
        video_id = (params.get("v") or [""])[0]
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        return video_id
    raise YouTubeNotFoundError(f"Could not extract YouTube video id from '{video_ref}'.")


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
