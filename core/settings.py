from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_url: str = Field(default="sqlite:///dal/local/app.sqlite")
    db_path: Path = Field(default=Path("dal/local/app.sqlite"))

    worker_poll_interval_seconds: float = Field(default=10.0, ge=0.1)
    worker_retry_max_attempts: int = Field(default=5, ge=0)
    worker_retry_backoff_seconds: float = Field(default=2.0, ge=0.0)
    worker_retry_backoff_multiplier: float = Field(default=2.0, ge=1.0)
    worker_retry_max_backoff_seconds: float = Field(default=120.0, ge=0.0)

    assets_root_dir: Path = Field(default=Path("dal/local/assets"))
    assets_videos_dir: Path = Field(default=Path("dal/local/assets/videos"))
    assets_img_dir: Path = Field(default=Path("dal/local/assets/img"))
    assets_audit_dir: Path = Field(default=Path("dal/local/assets/audit"))

    groq_api_key: str | None = Field(default=None)
    groq_model: str | None = Field(default=None)
    groq_base_url: str | None = Field(default=None)
    groq_plan_generation_enabled: bool = Field(default=False)
    groq_timeout_seconds: float = Field(default=20.0, gt=0)

    youtube_adapter_enabled: bool = Field(default=True)
    youtube_api_key: str | None = Field(default=None)
    youtube_base_url: str | None = Field(default=None)
    youtube_timeout_seconds: float = Field(default=30.0, gt=0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
