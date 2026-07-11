from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app import __version__
from app.models.manager import model_manager
from app.storage.database import check_db_health

router = APIRouter(prefix="/api/system")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_health = await check_db_health()
    return HealthResponse(
        version=__version__,
        status="ok",
        database=db_health,
        models=model_manager.get_status(),
    )


@router.get("/logs")
async def get_logs(page: int = 1, per_page: int = 50):
    return {"items": [], "page": page, "per_page": per_page}


@router.post("/backup")
async def create_backup():
    return {"status": "backup_created", "path": "/tmp/backup_placeholder"}


@router.post("/restore")
async def restore_backup():
    return {"status": "restore_started"}
