from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import HealthResponse
from app.config import settings
from app.models.manager import model_manager
from app.providers.registry import provider_registry

router = APIRouter(prefix="/api/models")


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
    return {
        "items": [
            {"name": "llama-3.2-1b", "size": "~800MB", "status": "not_downloaded"},
            {"name": "nomic-embed-text-v1.5", "size": "~200MB", "status": "not_downloaded"},
        ]
    }


@router.post("/download")
async def download_model(name: str = ""):
    if not name:
        raise HTTPException(status_code=400, detail="Model name required")
    return {"status": "download_started", "model": name}
