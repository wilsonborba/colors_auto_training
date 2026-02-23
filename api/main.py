from core.settings import app_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.routes.hello_route import hello_router
from presentation.routes.keyword_route import keyword_router

settings = app_settings()


app = FastAPI(
    root_path="/",
    root_path_in_servers=False,
    redirect_slashes=True,
    title="Color Auto Training API",
    description="API for Color Auto Training application",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello_router, tags=["hello_router"])
app.include_router(keyword_router, tags=["keyword_router"])
