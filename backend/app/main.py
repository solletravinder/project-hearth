from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.storage.database import init_db

from app.api import documents as documents_router
from app.api import chat as chat_router
from app.api import notes as notes_router
from app.api import conversations as conversations_router
from app.api import search as search_router
from app.api import settings as settings_router
from app.api import models_api as models_router
from app.api import system as system_router


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

    app.include_router(documents_router.router)
    app.include_router(chat_router.router)
    app.include_router(notes_router.router)
    app.include_router(conversations_router.router)
    app.include_router(search_router.router)
    app.include_router(settings_router.router)
    app.include_router(models_router.router)
    app.include_router(system_router.router)

    return app


app = create_app()
