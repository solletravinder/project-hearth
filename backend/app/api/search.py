from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

router = APIRouter(prefix="/api/search")


@router.get("/")
async def search(
    q: str = "",
    doc_type: Optional[str] = None,
    folder: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
):
    # Stub: return empty results
    return {
        "items": [],
        "total": 0,
        "page": page,
        "per_page": per_page,
        "query": q,
    }
