from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.api import chat as chat_router
from app.api import conversations as conversations_router
from app.api import documents as documents_router
from app.api import models_api as models_router
from app.api import notes as notes_router
from app.api import search as search_router
from app.api import settings as settings_router
from app.api import system as system_router
from app.config import settings
from app.storage.database import init_db


def create_app() -> FastAPI:
    """Application factory."""

    @asynccontextmanager
    async def lifespan(_app: FastAPI):  # noqa: ARG001
        await init_db()
        yield

    app = FastAPI(
        title="Hearth API",
        version=__version__,
        lifespan=lifespan,
        redirect_slashes=True,
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

    # ── Serve the built React frontend via Jinja2 template ─────────
    # The React build is served through Jinja2Templates, making it
    # a proper FastAPI-with-Jinja2 setup. We mount only the hashed
    # /assets folder directly (for JS/CSS bundles), then use a
    # catch-all route to render index.html via Jinja2 — enabling
    # React Router client-side navigation while keeping the template
    # engine in the loop for future server-side injection needs.
    frontend_dist: Path = settings.frontend_dist_dir.resolve()
    if frontend_dist.is_dir() and (frontend_dist / "index.html").exists():
        # Hashed static assets (JS/CSS bundles) — mount directly for performance
        assets_dir = frontend_dist / "assets"
        if assets_dir.is_dir():
            app.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="assets",
            )

        # Jinja2 template loader pointed at the build output directory
        templates = Jinja2Templates(directory=str(frontend_dist))

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_frontend(request: Request, full_path: str = ""):
            """Serve the React SPA via Jinja2 template.

            - Root path (/) renders index.html through Jinja2Templates.
            - Static root files (favicon.svg, manifest.json) are served
              directly as FileResponse.
            - All other non-API, non-asset paths render index.html via
              Jinja2 as SPA fallback for React Router client-side nav.
            - API and /assets paths never reach here — they are handled
              by earlier routes and the StaticFiles mount respectively.
            """
            # Root path → render index.html via Jinja2
            if not full_path:
                return templates.TemplateResponse(
                    request,
                    "index.html",
                    {"request": request},
                )

            # Serve exact file if it exists (favicon.svg, manifest.json, robots.txt)
            full_path_resolved: Path = frontend_dist / full_path
            if full_path_resolved.is_file():
                return FileResponse(str(full_path_resolved))

            # SPA fallback — render through Jinja2 template engine
            return templates.TemplateResponse(
                request,
                "index.html",
                {"request": request},
            )

    return app


app = create_app()
