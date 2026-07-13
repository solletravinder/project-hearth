import os
from pathlib import Path

import aiofiles

from app.config import settings


async def save_file(
    filename: str,
    content: bytes,
    subdir: str = "uploads",
) -> Path:
    """Save a file to the data directory. Returns the full path."""
    target_dir = settings.data_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / filename

    async with aiofiles.open(str(file_path), "wb") as f:
        await f.write(content)

    return file_path


async def read_file(
    filename: str,
    subdir: str = "uploads",
) -> bytes | None:
    """Read a file from the data directory. Returns None if not found."""
    file_path = settings.data_dir / subdir / filename
    if not file_path.exists():
        return None

    async with aiofiles.open(str(file_path), "rb") as f:
        return await f.read()


async def delete_file(
    filename: str,
    subdir: str = "uploads",
) -> bool:
    """Delete a file from the data directory. Returns True if deleted."""
    file_path = settings.data_dir / subdir / filename
    if not file_path.exists():
        return False

    os.remove(str(file_path))
    return True


async def get_disk_usage() -> dict:
    """Get disk usage info for the data directory."""
    data_dir = settings.data_dir
    total_size = 0
    file_count = 0

    if data_dir.exists():
        for entry in data_dir.rglob("*"):
            if entry.is_file():
                total_size += entry.stat().st_size
                file_count += 1

    return {
        "total_bytes": total_size,
        "file_count": file_count,
        "data_dir": str(data_dir),
    }
