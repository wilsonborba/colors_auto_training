from __future__ import annotations

from fastapi import FastAPI

from core.settings import get_settings
from presentation.routes.jobs_events import router as jobs_events_router
from presentation.routes.search_plans import router as search_plans_router
from presentation.routes.video_queue import router as video_queue_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="colors_auto_training API")
    app.state.settings = settings
    app.include_router(video_queue_router)
    app.include_router(jobs_events_router)
    app.include_router(search_plans_router)
    return app


app = create_app()
