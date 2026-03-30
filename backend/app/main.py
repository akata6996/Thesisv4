"""Application entrypoint for AEGIS FastAPI backend."""

from fastapi import FastAPI

from app.api.v1_router import api_v1_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
