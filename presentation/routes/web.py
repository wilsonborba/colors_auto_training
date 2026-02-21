from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter(tags=["web-ui"])

_WEB_ROOT = Path("presentation/web/pages")


@router.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/search-plans")


@router.get("/ui/search-plans")
def search_plans_page() -> FileResponse:
    return FileResponse(_WEB_ROOT / "search-plans-management" / "index.html")


@router.get("/ui/video-downloads")
def video_downloads_page() -> FileResponse:
    return FileResponse(_WEB_ROOT / "video-downloads-dashboard" / "index.html")
