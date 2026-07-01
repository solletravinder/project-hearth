from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.storage.database import check_db_health, init_db
from app.models.manager import model_manager


def create_app() -> FastAPI:
    """Application factory."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db()
        yield

    app = FastAPI(
        title="Hearth API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/system/health")
    async def health():
        db_health = await check_db_health()
        return {
            "version": "0.1.0",
            "status": "ok",
            "database": db_health,
            "models": model_manager.get_status(),
        }

    return app


app = create_app()
