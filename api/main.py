from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.settings import app_settings
from src.presentation.routes.hello import hello_router

settings = app_settings()


app = FastAPI(
    root_path="/",
    root_path_in_servers=False,
    redirect_slashes=True,
    title="Color Auto Training API",
    description="API for Accredit application",
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
