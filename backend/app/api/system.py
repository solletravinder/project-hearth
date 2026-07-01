from __future__ import annotations

from fastapi import APIRouter

from app.models.manager import model_manager
from app.storage.database import check_db_health

router = APIRouter(prefix="/api/system")


@router.get("/health")
async def health():
    db_health = await check_db_health()
    return {
        "version": "0.1.0",
        "status": "ok",
        "database": db_health,
        "models": model_manager.get_status(),
    }


@router.get("/logs")
async def get_logs(page: int = 1, per_page: int = 50):
    # Stub: return empty log list
    return {"items": [], "page": page, "per_page": per_page}


@router.post("/backup")
async def create_backup():
    # Stub: return backup info
    return {"status": "backup_created", "path": "/tmp/backup_placeholder"}


@router.post("/restore")
async def restore_backup():
    # Stub: return restore info
    return {"status": "restore_started"}
