import asyncio
import json
import logging

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import HealthResponse
from app.config import settings
from app.models.manager import model_manager
from app.providers.registry import provider_registry

router = APIRouter(prefix="/api/models")
logger = logging.getLogger(__name__)

# ── Model registry ─────────────────────────────────────────────────────────
# Maps logical name → (filename, HuggingFace direct-download URL)
MODEL_REGISTRY: dict[str, tuple[str, str]] = {
    "nomic-embed-text-v1.5": (
        "nomic-embed-text-v1.5.Q4_K_M.gguf",
        "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/"
        "nomic-embed-text-v1.5.Q4_K_M.gguf",
    ),
    "llama-3.2-1b": (
        "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/"
        "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
    ),
}

# ── In-memory download progress tracker ───────────────────────────────────
# key: model name  →  {"status": str, "downloaded": int, "total": int, ...}
_download_progress: dict[str, dict] = {}


async def _do_download(model_name: str, filename: str, url: str) -> None:
    """Stream-download a GGUF model from *url* into models_dir.

    Progress is written to _download_progress[model_name] so the SSE
    endpoint can poll it without touching the filesystem on every tick.
    """
    models_dir = settings.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)
    dest = models_dir / filename

    _download_progress[model_name] = {
        "status": "downloading",
        "downloaded": 0,
        "total": 0,
        "filename": filename,
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client, \
                client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            _download_progress[model_name]["total"] = total

            with open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=65_536):  # 64 KB
                    f.write(chunk)
                    _download_progress[model_name]["downloaded"] += len(chunk)

        _download_progress[model_name]["status"] = "done"
        logger.info("Model download complete: %s → %s", model_name, dest)

    except Exception as exc:
        _download_progress[model_name]["status"] = "error"
        _download_progress[model_name]["error"] = str(exc)
        logger.error("Model download failed for %s: %s", model_name, exc)
        # Remove incomplete file so a retry starts clean
        if dest.exists():
            dest.unlink(missing_ok=True)


# ── Existing endpoints (unchanged behaviour) ───────────────────────────────

@router.get("/status", response_model=HealthResponse)
async def model_status() -> HealthResponse:
    await provider_registry.get_status()
    return HealthResponse(
        version="0.1.0",
        status="ok",
        database={},
        models=model_manager.get_status(),
    )


@router.get("/providers")
async def get_providers():
    return await provider_registry.get_status()


@router.get("/profiles")
async def get_profiles():
    return {"profiles": settings.profiles, "active": settings.active_profile}


@router.post("/profile")
async def set_profile(body: dict):
    profile = body.get("profile", "")
    if profile not in settings.profiles:
        raise HTTPException(status_code=400, detail=f"Unknown profile: {profile}")
    return {"profile": profile, "config": settings.profiles[profile]}


@router.post("/unload/{name}")
async def unload_model(name: str):
    success = model_manager.unload(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not loaded")
    return {"status": "unloaded", "model": name}


@router.get("/downloads")
async def list_downloads():
    """List all known downloadable models with their current status."""
    models_dir = settings.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)

    items = []
    for name, (filename, _url) in MODEL_REGISTRY.items():
        dest = models_dir / filename
        progress = _download_progress.get(name, {})

        # A file > 1 KiB is treated as a real model
        # (guards against stale mock placeholder text files from old code)
        if dest.exists() and dest.stat().st_size > 1024:
            status = "downloaded"
            size_label = f"~{round(dest.stat().st_size / 1024 / 1024)} MB"
        elif progress.get("status") == "downloading":
            status = "downloading"
            size_label = "—"
        elif progress.get("status") == "error":
            status = "error"
            size_label = "—"
        else:
            status = "not_downloaded"
            size_label = "—"

        items.append({
            "name": name,
            "filename": filename,
            "size": size_label,
            "status": status,
            "progress": progress,
        })

    return {"items": items}


# ── Download endpoints ─────────────────────────────────────────────────────

@router.post("/download")
async def download_model(name: str = "", body: dict | None = None):
    """Start a real background download for a named model.

    Accepts the model name either as a query-string param (?name=…)
    or as a JSON body field ("name" or "model").  Returns immediately;
    poll ``GET /api/models/download/{name}/progress`` for SSE updates.
    """
    # Resolve model name from query param or request body
    model_name = name
    if not model_name and body:
        model_name = body.get("name", "") or body.get("model", "")

    if not model_name:
        raise HTTPException(status_code=400, detail="Model name required")

    if model_name not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown model '{model_name}'. "
                f"Available: {list(MODEL_REGISTRY.keys())}"
            ),
        )

    # Idempotency: don't start a second download while one is in progress
    existing = _download_progress.get(model_name, {})
    if existing.get("status") == "downloading":
        return {"status": "already_downloading", "model": model_name}

    filename, url = MODEL_REGISTRY[model_name]
    dest = settings.models_dir / filename
    if dest.exists() and dest.stat().st_size > 1024:
        return {"status": "already_downloaded", "model": model_name, "filename": filename}

    # Fire-and-forget background task (non-blocking)
    asyncio.create_task(_do_download(model_name, filename, url))

    return {
        "status": "started",
        "model": model_name,
        "filename": filename,
        "url": url,
    }


@router.get("/download/{name}/progress")
async def download_progress_stream(name: str):
    """SSE endpoint that streams live download progress for *name*.

    Emits a JSON ``data:`` line every 500 ms until status is
    ``"done"`` or ``"error"``, then closes the stream.
    """
    if name not in MODEL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown model '{name}'")

    async def _events():
        while True:
            progress = _download_progress.get(name, {"status": "idle"})
            yield f"data: {json.dumps(progress)}\n\n"
            if progress.get("status") in ("done", "error"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(_events(), media_type="text/event-stream")
