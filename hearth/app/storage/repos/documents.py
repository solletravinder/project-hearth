from __future__ import annotations

import json
from typing import Any

from app.storage.database import get_db
from app.storage.repos._shared import _deserialize_metadata, _new_id, _now, _row_to_dict


async def create_document(
    title: str,
    doc_type: str,
    folder: str = "default",
    file_path: str | None = None,
    file_size: int = 0,
    mime_type: str | None = None,
    metadata: dict[str, Any] | None = None,
    word_count: int = 0,
    doc_id: str | None = None,
) -> dict[str, Any]:
    doc_id = doc_id or _new_id()
    now = _now()
    conn = await get_db()
    try:
        await conn.execute(
            """INSERT INTO documents (id, title, doc_type, folder, file_path, file_size,
               mime_type, metadata, word_count, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_id,
                title,
                doc_type,
                folder,
                file_path,
                file_size,
                mime_type,
                json.dumps(metadata) if metadata else None,
                word_count,
                now,
                now,
            ),
        )
        await conn.commit()
        result = await get_document(doc_id)
        assert result is not None
        return result
    finally:
        await conn.close()


async def get_document(doc_id: str) -> dict[str, Any] | None:
    conn = await get_db()
    try:
        cursor = await conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = await cursor.fetchone()
        return _deserialize_metadata(_row_to_dict(row))
    finally:
        await conn.close()


async def list_documents(
    folder: str | None = None,
    doc_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    conn = await get_db()
    try:
        conditions: list[str] = []
        params: list[Any] = []

        if folder:
            conditions.append("folder = ?")
            params.append(folder)
        if doc_type:
            conditions.append("doc_type = ?")
            params.append(doc_type)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM documents WHERE {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        results: list[dict[str, Any]] = []
        for r in rows:
            row_dict = _deserialize_metadata(_row_to_dict(r))
            if row_dict:
                results.append(row_dict)
        return results
    finally:
        await conn.close()


async def update_document_status(
    doc_id: str, status: str, metadata: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    conn = await get_db()
    try:
        now = _now()
        if metadata:
            existing = await get_document(doc_id)
            existing_meta = existing.get("metadata") if existing else None
            merged = dict(existing_meta) if existing_meta else {}
            merged.update(metadata)
            await conn.execute(
                "UPDATE documents SET status = ?, metadata = ?, updated_at = ? WHERE id = ?",
                (status, json.dumps(merged), now, doc_id),
            )
        else:
            await conn.execute(
                "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, doc_id),
            )
        await conn.commit()
        return await get_document(doc_id)
    finally:
        await conn.close()


async def delete_document(doc_id: str) -> bool:
    conn = await get_db()
    try:
        cursor = await conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()
