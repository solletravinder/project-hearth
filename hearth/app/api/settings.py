from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.schemas import SettingsResponse
from app.storage.repos.settings import get_settings, update_setting

router = APIRouter(prefix="/api/settings")


@router.get("/", response_model=SettingsResponse)
async def get_settings_endpoint() -> SettingsResponse:
    raw = await get_settings()
    typed: dict[str, Any] = {}
    for key, value in raw.items():
        typed[key] = _coerce_value(key, value)
    return SettingsResponse(settings=typed)


@router.put("/", response_model=SettingsResponse)
async def update_settings_endpoint(body: dict[str, Any]) -> SettingsResponse:
    updated: dict[str, Any] = {}
    for key, value in body.items():
        str_value = str(value).lower() if isinstance(value, bool) else str(value)
        result = await update_setting(key, str_value)
        updated[key] = _coerce_value(key, result["value"])
    return SettingsResponse(settings=updated)


# Settings that should be numbers or booleans rather than raw strings
_NUMERIC_KEYS = {
    "max_tokens", "temperature", "top_k", "top_p",
    "chunk_size", "chunk_overlap", "search_result_count",
}
_BOOL_KEYS = {"pii_filter_enabled"}


def _coerce_value(key: str, value: str) -> str | int | float | bool:
    if key in _BOOL_KEYS:
        return value.lower() == "true"
    if key in _NUMERIC_KEYS:
        try:
            if key in {"temperature", "top_p"}:
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            return value
    return value
