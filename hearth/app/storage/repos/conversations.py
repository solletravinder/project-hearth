
from typing import Any

from app.storage.database import get_db
from app.storage.repos._shared import _new_id, _now, _row_to_dict


async def create_conversation(
    title: str = "New Conversation",
    model: str = "default",
    system_prompt: str = "",
    branch_from: str | None = None,
) -> dict[str, Any]:
    conv_id = _new_id()
    now = _now()
    conn = await get_db()
    try:
        await conn.execute(
            "INSERT INTO conversations "
            "(id, title, model, system_prompt, branch_from, "
            "created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conv_id, title, model, system_prompt, branch_from, now, now),
        )
        await conn.commit()
        cursor = await conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        row = await cursor.fetchone()
        result = _row_to_dict(row)
        assert result is not None
        return result
    finally:
        await conn.close()


async def list_conversations(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    conn = await get_db()
    try:
        cursor = await conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [r for r in (_row_to_dict(r) for r in rows) if r is not None]
    finally:
        await conn.close()


async def get_conversation(conv_id: str) -> dict[str, Any] | None:
    conn = await get_db()
    try:
        cursor = await conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        row = await cursor.fetchone()
        return _row_to_dict(row)
    finally:
        await conn.close()


async def delete_conversation(conv_id: str) -> bool:
    conn = await get_db()
    try:
        cursor = await conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()
