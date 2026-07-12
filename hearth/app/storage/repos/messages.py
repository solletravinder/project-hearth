import json
from typing import Any

from app.storage.database import get_db
from app.storage.repos._shared import _new_id, _now, _row_to_dict


async def create_message(
    conversation_id: str,
    role: str,
    content: str,
    context_docs: list[str] | None = None,
    citations: list[dict] | None = None,
    token_count: int | None = None,
    generation_ms: int | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> dict[str, Any]:
    msg_id = _new_id()
    conn = await get_db()
    try:
        await conn.execute(
            "INSERT INTO messages "
            "(id, conversation_id, role, content, context_docs, citations, "
            "token_count, generation_ms, tokens_in, tokens_out) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                msg_id,
                conversation_id,
                role,
                content,
                json.dumps(context_docs) if context_docs else None,
                json.dumps(citations) if citations else None,
                token_count or 0,
                generation_ms or 0,
                tokens_in,
                tokens_out,
            ),
        )
        await conn.execute(
            "UPDATE conversations "
            "SET message_count = message_count + 1, updated_at = ? "
            "WHERE id = ?",
            (_now(), conversation_id),
        )
        await conn.commit()
        cursor = await conn.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
        row = await cursor.fetchone()
        result = _row_to_dict(row)
        assert result is not None
        return result
    finally:
        await conn.close()


async def get_messages(
    conversation_id: str, limit: int = 100, offset: int = 0
) -> list[dict[str, Any]]:
    conn = await get_db()
    try:
        cursor = await conn.execute(
            "SELECT * FROM messages "
            "WHERE conversation_id = ? "
            "ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (conversation_id, limit, offset),
        )
        rows = await cursor.fetchall()
        results = []
        for r in (_row_to_dict(r) for r in rows):
            if r is None:
                continue
            if r.get("context_docs"):
                try:
                    r["context_docs"] = json.loads(r["context_docs"])
                except (json.JSONDecodeError, TypeError):
                    r["context_docs"] = None
            if r.get("citations"):
                try:
                    r["citations"] = json.loads(r["citations"])
                except (json.JSONDecodeError, TypeError):
                    r["citations"] = None
            results.append(r)
        return results
    finally:
        await conn.close()
