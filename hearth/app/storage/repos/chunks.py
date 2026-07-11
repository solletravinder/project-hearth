from __future__ import annotations

from typing import Any

from app.storage.database import get_db
from app.storage.repos._shared import _new_id, _row_to_dict


async def create_chunk(
    document_id: str,
    chunk_index: int,
    content: str,
    token_count: int = 0,
    content_hash: str | None = None,
    embedding: bytes | None = None,
) -> dict[str, Any]:
    chunk_id = _new_id()
    conn = await get_db()
    try:
        await conn.execute(
            """INSERT INTO chunks (id, document_id, chunk_index, content, token_count,
               content_hash, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chunk_id, document_id, chunk_index, content, token_count, content_hash, embedding),
        )
        await conn.commit()
        cursor = await conn.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
        row = await cursor.fetchone()
        result = _row_to_dict(row)
        assert result is not None
        return result
    finally:
        await conn.close()


async def rebuild_fts() -> bool:
    """Rebuild the FTS5 index from the chunks table."""
    conn = await get_db()
    try:
        await conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        await conn.commit()
        return True
    except Exception:
        return False
    finally:
        await conn.close()


async def get_chunks_for_document(document_id: str) -> list[dict[str, Any]]:
    conn = await get_db()
    try:
        cursor = await conn.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index ASC",
            (document_id,),
        )
        rows = await cursor.fetchall()
        return [r for r in (_row_to_dict(r) for r in rows) if r is not None]
    finally:
        await conn.close()
