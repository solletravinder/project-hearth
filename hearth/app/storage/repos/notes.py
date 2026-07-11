from __future__ import annotations

import json
from typing import Any

from app.storage.database import get_db
from app.storage.repos._shared import _new_id, _now, _row_to_dict


async def create_note(
    title: str,
    content: str = "",
    folder: str = "default",
    tags: list[str] | None = None,
    pinned: bool = False,
    source_document_id: str | None = None,
) -> dict[str, Any]:
    note_id = _new_id()
    now = _now()
    conn = await get_db()
    try:
        await conn.execute(
            "INSERT INTO notes "
            "(id, title, content, folder, tags, pinned, "
            "source_document_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                note_id,
                title,
                content,
                folder,
                json.dumps(tags) if tags else None,
                1 if pinned else 0,
                source_document_id,
                now,
                now,
            ),
        )
        await conn.commit()
        cursor = await conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = await cursor.fetchone()
        result = _row_to_dict(row)
        assert result is not None
        return result
    finally:
        await conn.close()


async def get_note(note_id: str) -> dict[str, Any] | None:
    conn = await get_db()
    try:
        cursor = await conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = await cursor.fetchone()
        result = _row_to_dict(row)
        if result and result.get("tags"):
            try:
                result["tags"] = json.loads(result["tags"])
            except (json.JSONDecodeError, TypeError):
                result["tags"] = None
        return result
    finally:
        await conn.close()


async def list_notes(
    folder: str | None = None,
    pinned: bool | None = None,
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
        if pinned is not None:
            conditions.append("pinned = ?")
            params.append(1 if pinned else 0)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = (
            f"SELECT * FROM notes WHERE {where} "
            "ORDER BY pinned DESC, updated_at DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        results = []
        for r in (_row_to_dict(r) for r in rows):
            if r is None:
                continue
            if r.get("tags"):
                try:
                    r["tags"] = json.loads(r["tags"])
                except (json.JSONDecodeError, TypeError):
                    r["tags"] = None
            results.append(r)
        return results
    finally:
        await conn.close()


async def update_note(
    note_id: str,
    title: str | None = None,
    content: str | None = None,
    folder: str | None = None,
    tags: list[str] | None = None,
    pinned: bool | None = None,
) -> dict[str, Any] | None:
    conn = await get_db()
    try:
        fields: list[str] = []
        params: list[Any] = []

        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if content is not None:
            fields.append("content = ?")
            params.append(content)
        if folder is not None:
            fields.append("folder = ?")
            params.append(folder)
        if tags is not None:
            fields.append("tags = ?")
            params.append(json.dumps(tags))
        if pinned is not None:
            fields.append("pinned = ?")
            params.append(1 if pinned else 0)

        if not fields:
            return await get_note(note_id)

        fields.append("updated_at = ?")
        params.append(_now())
        params.append(note_id)

        await conn.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id = ?", params)
        await conn.commit()
        return await get_note(note_id)
    finally:
        await conn.close()


async def delete_note(note_id: str) -> bool:
    conn = await get_db()
    try:
        cursor = await conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()
