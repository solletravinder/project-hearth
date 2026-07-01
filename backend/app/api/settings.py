from __future__ import annotations

from typing import Dict

from pydantic import BaseModel
from fastapi import APIRouter

from app.storage.repository import get_settings, update_setting

router = APIRouter(prefix="/api/settings")


class UpdateSettingsRequest(BaseModel):
    settings: Dict[str, str]


@router.get("/")
async def get_settings_endpoint():
    settings_dict = await get_settings()
    return {"settings": settings_dict}


@router.put("/")
async def update_settings_endpoint(body: UpdateSettingsRequest):
    updated = {}
    for key, value in body.settings.items():
        result = await update_setting(key, value)
        updated[key] = result["value"]
    return {"settings": updated}
