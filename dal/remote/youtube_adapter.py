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

from core.settings import get_settings


def get_youtube_adapter_config() -> dict[str, object | None]:
    """Return YouTube adapter configuration from centralized settings."""
    settings = get_settings()
    return {
        "enabled": settings.youtube_adapter_enabled,
        "api_key": settings.youtube_api_key,
        "base_url": settings.youtube_base_url,
        "timeout_seconds": settings.youtube_timeout_seconds,
    }
