from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.settings import get_settings
from presentation.api.routes.jobs_events import router as jobs_events_router
from presentation.api.routes.search_plans import router as search_plans_router
from presentation.api.routes.video_queue import router as video_queue_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="colors_auto_training API")
    app.state.settings = settings

    app.include_router(video_queue_router)
    app.include_router(jobs_events_router)
    app.include_router(search_plans_router)

    web_root = Path(__file__).resolve().parents[1] / "web"
    app.mount("/web", StaticFiles(directory=str(web_root), html=True), name="web")

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/web/pages/video-downloads-dashboard/index.html")

    return app


app = create_app()
