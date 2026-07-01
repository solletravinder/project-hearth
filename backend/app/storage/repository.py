from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from app.storage.database import get_db


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


# ─── Documents ─────────────────────────────────────────────────────────────────


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
        result = _row_to_dict(row)
        if result and result.get("metadata"):
            result["metadata"] = json.loads(result["metadata"])
        return result
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
            row_dict = _row_to_dict(r)
            if row_dict:
                if row_dict.get("metadata"):
                    row_dict["metadata"] = json.loads(row_dict["metadata"])
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


# ─── Chunks ────────────────────────────────────────────────────────────────────


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
    """Rebuild the FTS5 index from the chunks table.
    Only works with external content FTS5 tables.
    """
    conn = await get_db()
    try:
        await conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        await conn.commit()
        return True
    except Exception:
        return False
    finally:
        await conn.close()


# ─── Conversations ─────────────────────────────────────────────────────────────


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


# ─── Messages ──────────────────────────────────────────────────────────────────


async def create_message(
    conversation_id: str,
    role: str,
    content: str,
    context_docs: list[str] | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> dict[str, Any]:
    msg_id = _new_id()
    conn = await get_db()
    try:
        await conn.execute(
            "INSERT INTO messages "
            "(id, conversation_id, role, content, context_docs, "
            "tokens_in, tokens_out) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                msg_id,
                conversation_id,
                role,
                content,
                json.dumps(context_docs) if context_docs else None,
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
        return [r for r in (_row_to_dict(r) for r in rows) if r is not None]
    finally:
        await conn.close()


# ─── Notes ─────────────────────────────────────────────────────────────────────


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
        return _row_to_dict(row)
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
        return [r for r in (_row_to_dict(r) for r in rows) if r is not None]
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


# ─── Settings ──────────────────────────────────────────────────────────────────


async def get_settings() -> dict[str, str]:
    conn = await get_db()
    try:
        cursor = await conn.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}
    finally:
        await conn.close()


async def update_setting(key: str, value: str) -> dict[str, str]:
    conn = await get_db()
    try:
        await conn.execute(
            "INSERT INTO settings (key, value, updated_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE "
            "SET value = excluded.value, updated_at = excluded.updated_at",
            (key, value, _now()),
        )
        await conn.commit()
        return {"key": key, "value": value}
    finally:
        await conn.close()
