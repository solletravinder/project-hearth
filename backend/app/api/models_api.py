from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.manager import model_manager

router = APIRouter(prefix="/api/models")


class ProfileRequest(BaseModel):
    profile: str


@router.get("/status")
async def model_status():
    """Return loaded models status."""
    return model_manager.get_status()


@router.get("/profiles")
async def get_profiles():
    """Return available performance profiles."""
    return {"profiles": settings.profiles}


@router.post("/profile")
async def set_profile(body: ProfileRequest):
    """Set the active performance profile (stub)."""
    if body.profile not in settings.profiles:
        raise HTTPException(status_code=400, detail=f"Unknown profile: {body.profile}")
    return {"profile": body.profile, "config": settings.profiles[body.profile]}


@router.post("/unload/{name}")
async def unload_model(name: str):
    """Unload a model by name."""
    success = model_manager.unload(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not loaded")
    return {"status": "unloaded", "model": name}


@router.get("/downloads")
async def list_downloads():
    """List available models for download (stub)."""
    return {
        "items": [
            {"name": "llama-3.2-1b", "size": "~800MB", "status": "not_downloaded"},
            {"name": "nomic-embed-text-v1.5", "size": "~200MB", "status": "not_downloaded"},
        ]
    }


@router.post("/download")
async def download_model(name: str = ""):
    """Download a model (stub)."""
    if not name:
        raise HTTPException(status_code=400, detail="Model name required")
    return {"status": "download_started", "model": name}
