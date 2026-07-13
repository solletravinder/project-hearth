import asyncio
import logging
from contextlib import suppress

import aiosqlite

from app.config import settings
from app.storage.schema import INIT_SQL

logger = logging.getLogger(__name__)

_db_semaphore = asyncio.Semaphore(10)
_connection_cache: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Return an async SQLite connection to the app database (reused within the same task)."""
    db_path = settings.resolved_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with _db_semaphore:
        conn = await aiosqlite.connect(str(db_path))
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA foreign_keys=ON;")

        import sqlite_vec
        await conn.enable_load_extension(True)
        await conn.load_extension(sqlite_vec.loadable_path())

        return conn


async def init_db() -> None:
    """Create all tables if they do not exist."""
    conn = await get_db()
    try:
        await conn.executescript(INIT_SQL)

        # Add new columns to messages table if they don't exist
        for col_def in [
            ("citations", "TEXT"),
            ("token_count", "INTEGER DEFAULT 0"),
            ("generation_ms", "INTEGER DEFAULT 0"),
        ]:
            with suppress(Exception):
                await conn.execute(f"ALTER TABLE messages ADD COLUMN {col_def[0]} {col_def[1]};")

        await conn.commit()
        logger.info("Database initialized")
    finally:
        await conn.close()


async def check_db_health() -> dict:
    """Check database health and return status info."""
    conn = await get_db()
    try:
        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM documents")
        row = await cursor.fetchone()
        assert row is not None
        doc_count = row["cnt"]

        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM chunks")
        row = await cursor.fetchone()
        assert row is not None
        chunk_count = row["cnt"]

        return {
            "status": "ok",
            "doc_count": doc_count,
            "chunk_count": chunk_count,
        }
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return {
            "status": "error",
            "detail": str(e),
        }
    finally:
        await conn.close()
