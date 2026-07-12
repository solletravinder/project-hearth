import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app import __version__
from app.api.schemas import HealthResponse
from app.config import settings
from app.models.manager import model_manager
from app.storage.database import check_db_health, get_db

router = APIRouter(prefix="/api/system")
logger = logging.getLogger(__name__)


def detect_gpu() -> dict:
    """Detect GPU via nvidia-smi or wmic. Returns {available, model} with no hardcoded fallback."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            name = result.stdout.strip()
            if name:
                return {"available": True, "model": name}
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    try:
        result = subprocess.run(
            ["wmic", "path", "win32_videocontroller", "get", "name"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
            # First line is header "Name", subsequent lines are values
            for line in lines[1:]:
                if line and line.lower() != "name":
                    return {"available": True, "model": line}
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return {"available": False, "model": None}


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_health = await check_db_health()
    return HealthResponse(
        version=__version__,
        status="ok",
        database=db_health,
        models=model_manager.get_status(),
    )


@router.get("/info")
async def system_info():
    """Return system hardware and platform information."""
    import psutil
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(str(settings.data_dir))
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count() or 0,
        "ram": {
            "total_gb": round(mem.total / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 1),
            "free_gb": round(disk.free / (1024**3), 1),
        },
        "gpu": detect_gpu(),
        "python_version": platform.python_version(),
    }


@router.get("/logs")
async def get_logs(page: int = 1, per_page: int = 50):
    db = await get_db()
    try:
        offset = (page - 1) * per_page
        cursor = await db.execute(
            "SELECT * FROM trace_log ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        rows = await cursor.fetchall()
        
        count_cursor = await db.execute("SELECT COUNT(*) FROM trace_log")
        total_row = await count_cursor.fetchone()
        total = total_row[0] if total_row else 0
        
        return {
            "items": [dict(r) for r in rows],
            "page": page,
            "per_page": per_page,
            "total": total
        }
    finally:
        await db.close()


@router.post("/backup")
async def create_backup():
    db_path = settings.resolved_db_path
    uploads_dir = settings.data_dir / "uploads"
    
    backups_dir = settings.data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    
    backup_filename = f"hearth_backup_{int(time.time())}.zip"
    backup_path = backups_dir / backup_filename
    
    def make_zip():
        with zipfile.ZipFile(str(backup_path), 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Backup DB file
            if db_path.exists():
                zip_file.write(str(db_path), db_path.name)
            # 2. Backup upload documents
            if uploads_dir.exists():
                for root, _, files in os.walk(str(uploads_dir)):
                    for file in files:
                        full_path = Path(root) / file
                        relative_path = Path("uploads") / full_path.relative_to(uploads_dir)
                        zip_file.write(str(full_path), str(relative_path))
                        
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, make_zip)
        return {
            "status": "backup_created",
            "filename": backup_filename,
            "path": str(backup_path)
        }
    except Exception as e:
        logger.error("Backup creation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Backup failed: {e}")


@router.post("/restore")
async def restore_backup(filename: str = ""):
    backups_dir = settings.data_dir / "backups"
    
    if filename:
        backup_path = backups_dir / filename
    else:
        # Restore latest backup
        backups = list(backups_dir.glob("hearth_backup_*.zip"))
        if not backups:
            raise HTTPException(status_code=404, detail="No backup files found")
        backups.sort(key=lambda x: x.stat().st_mtime)
        backup_path = backups[-1]
        
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail=f"Backup file not found: {backup_path.name}")
        
    db_path = settings.resolved_db_path
    uploads_dir = settings.data_dir / "uploads"
    
    def extract_zip():
        # Clear uploads folder first
        if uploads_dir.exists():
            shutil.rmtree(str(uploads_dir))
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(str(backup_path), 'r') as zip_file:
            for item in zip_file.namelist():
                if item == db_path.name:
                    zip_file.extract(item, path=str(db_path.parent))
                elif item.startswith("uploads/"):
                    zip_file.extract(item, path=str(settings.data_dir))
                    
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, extract_zip)
        return {
            "status": "restore_completed",
            "restored_from": backup_path.name
        }
    except Exception as e:
        logger.error("Backup restoration failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Restore failed: {e}")
