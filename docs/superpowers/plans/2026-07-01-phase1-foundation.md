# Phase 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Working shell — FastAPI backend starts, SQLite DB initializes with all schema tables, React frontend loads with layout shell, and both can communicate.

**Architecture:** Two independent workstreams in parallel — Python backend (FastAPI + SQLite + LangGraph) and React frontend (Vite + Tailwind + Zustand). Backend owns all data and ML inference; frontend is a SPA communicating via REST + SSE. Phase 1 produces skeleton code only — no model integration, no pipeline logic.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, SQLite + sqlite-vec + FTS5, LangGraph (Python), React 18, Vite, Tailwind CSS, Zustand, TypeScript

## Global Constraints

- Zero data leaves the machine — no telemetry, no analytics, no outbound connections
- Backend serves on port 8765, frontend dev server on port 5173
- All file paths, model caches, and DB live under `backend/data/` and `backend/models/`
- Python models directory (`backend/models/`) is gitignored via `.gitignore`
- Frontend proxies `/api/*` to backend during development via Vite proxy config
- The spec at `docs/superpowers/specs/2026-07-01-hearth-design.md` is the authoritative design reference
- No real model downloading or ML inference in Phase 1 — all model classes are stubs with mock responses

---

## Task 1: Backend Foundation

**Branch:** `feat/backend-foundation`

**Goal:** Python project scaffold, config, DB schema initialization, storage layer, core utilities, app factory. Everything needed for `uvicorn app.main:app` to start and serve a health endpoint with a live DB.

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/chunking.py`
- Create: `backend/app/core/pii.py`
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/database.py`
- Create: `backend/app/storage/repository.py`
- Create: `backend/app/storage/file_store.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/manager.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_storage.py`
- Create: `backend/tests/test_core.py`
- Create: `backend/Dockerfile`
- Create: `backend/data/.gitkeep`
- Create: `backend/models/.gitkeep`

**Interfaces (shared contract for all backend tasks):**
- `app.config.settings` — Pydantic `BaseSettings` with all paths, port, profiles
- `app.storage.database.get_db()` — returns async `sqlite3.Connection` with vec0 + FTS5 loaded
- `app.main.create_app()` — FastAPI app factory with CORS, static serving, router includes
- `app.models.manager.model_manager` — singleton stub returning empty status

---

- [ ] **Step 1.1: Create project config files**

Save `backend/pyproject.toml`:

```toml
[project]
name = "hearth"
version = "0.1.0"
description = "Fully offline, on-device notes & research assistant"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlite-vec>=0.1.0",
    "langgraph>=0.2.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-multipart>=0.0.12",
    "aiofiles>=24.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.28.0",
]
```

Save `backend/requirements.txt`:

```
# Hearth backend
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlite-vec>=0.1.0
langgraph>=0.2.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.12
aiofiles>=24.0.0

# Dev
pytest>=8.0.0
pytest-asyncio>=0.24.0
pytest-cov>=5.0.0
httpx>=0.28.0
```

- [ ] **Step 1.2: Create config module**

Save `backend/app/__init__.py` — empty file.

Save `backend/app/config.py`:

```python
"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Hearth application settings."""

    # Host / port
    host: str = "127.0.0.1"
    port: int = 8765

    # Directories
    data_dir: Path = Path("data")
    models_dir: Path = Path("models")

    # Database
    db_path: Path | None = None  # defaults to data_dir / "hearth.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Model profiles
    profiles: dict[str, dict] = {
        "fast": {
            "generator": "Qwen3-0.6B",
            "embeddings": "gte-small",
            "asr": "whisper-tiny",
            "verify": "Qwen3-0.6B",
            "size_gb": 0.7,
            "min_ram_gb": 8,
        },
        "balanced": {
            "generator": "Qwen2.5-1.5B",
            "embeddings": "gte-small",
            "asr": "whisper-base",
            "verify": "Qwen3-0.6B",
            "size_gb": 1.3,
            "min_ram_gb": 8,
        },
        "accurate": {
            "generator": "Llama-3.2-3B",
            "embeddings": "bge-base",
            "asr": "whisper-small",
            "verify": "Qwen3-0.6B",
            "size_gb": 3.0,
            "min_ram_gb": 16,
        },
    }

    @property
    def resolved_db_path(self) -> Path:
        return self.db_path or self.data_dir / "hearth.db"

    model_config = {"env_prefix": "HEARTH_", "frozen": False}


settings = Settings()
```

- [ ] **Step 1.3: Create database module**

Save `backend/app/storage/__init__.py` — empty.

Save `backend/app/storage/database.py`:

```python
"""SQLite database initialization with sqlite-vec and FTS5 support."""

from __future__ import annotations

import sqlite3
import aiosqlite
from pathlib import Path

from app.config import settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    doc_type    TEXT NOT NULL CHECK(doc_type IN ('pdf','image','audio','note','text')),
    mime_type   TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    file_size   INTEGER NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending','processing','ready','error')),
    error_msg   TEXT,
    source_info TEXT,
    folder_path TEXT DEFAULT '/',
    tags        TEXT DEFAULT '[]',
    checksum    TEXT,
    version     INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    id              TEXT PRIMARY KEY,
    document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    token_count     INTEGER NOT NULL,
    embedding       BLOB,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(document_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content, document_id UNINDEXED,
    tokenize='porter unicode61'
);

CREATE TABLE IF NOT EXISTS notes (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    tags        TEXT DEFAULT '[]',
    folder_path TEXT DEFAULT '/',
    is_pinned   INTEGER DEFAULT 0,
    is_archived INTEGER DEFAULT 0,
    checksum    TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id       TEXT PRIMARY KEY,
    title    TEXT NOT NULL,
    model    TEXT,
    context_docs TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content         TEXT NOT NULL,
    citations       TEXT,
    pii_redacted    INTEGER DEFAULT 0,
    parent_id       TEXT,
    token_count     INTEGER,
    generation_ms   INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);

CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trace_log (
    id          TEXT PRIMARY KEY,
    run_id      TEXT NOT NULL,
    node_name   TEXT NOT NULL,
    node_input  TEXT,
    node_output TEXT,
    duration_ms INTEGER,
    token_count INTEGER,
    success     INTEGER DEFAULT 1,
    error_msg   TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_trace_run ON trace_log(run_id);
"""


async def get_db() -> aiosqlite.Connection:
    """Return an async SQLite connection with loaded extensions."""
    db_path = settings.resolved_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row

    # Enable WAL mode for concurrent reads
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")

    return db


async def init_db() -> None:
    """Initialize the database schema."""
    db = await get_db()
    try:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    finally:
        await db.close()


async def check_db_health() -> dict:
    """Quick health check against the database."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM documents")
        doc_count = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM chunks")
        chunk_count = (await cursor.fetchone())[0]
        return {"status": "ok", "documents": doc_count, "chunks": chunk_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await db.close()
```

- [ ] **Step 1.4: Create storage modules**

Save `backend/app/storage/repository.py`:

```python
"""Data access layer for all entities."""

from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from app.storage.database import get_db


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Documents ──────────────────────────────────────────────

async def create_document(
    title: str,
    doc_type: str,
    mime_type: str,
    file_path: str,
    file_size: int,
    **extra: Any,
) -> dict:
    doc_id = _new_id()
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO documents (id, title, doc_type, mime_type, file_path, file_size, source_info, folder_path, tags, checksum)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_id, title, doc_type, mime_type, file_path, file_size,
                json.dumps(extra.get("source_info", {})),
                extra.get("folder_path", "/"),
                json.dumps(extra.get("tags", [])),
                extra.get("checksum"),
            ),
        )
        await db.commit()
        return await get_document(doc_id)
    finally:
        await db.close()


async def get_document(doc_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_documents(
    status: str | None = None,
    doc_type: str | None = None,
    folder: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> list[dict]:
    db = await get_db()
    try:
        where = []
        params: list[Any] = []
        if status:
            where.append("status = ?"); params.append(status)
        if doc_type:
            where.append("doc_type = ?"); params.append(doc_type)
        if folder:
            where.append("folder_path = ?"); params.append(folder)
        clause = " AND ".join(where) if where else "1"
        offset = (page - 1) * per_page
        cursor = await db.execute(
            f"SELECT * FROM documents WHERE {clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [*params, per_page, offset],
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def update_document_status(doc_id: str, status: str, error_msg: str | None = None) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE documents SET status = ?, error_msg = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, error_msg, doc_id),
        )
        await db.commit()
    finally:
        await db.close()


async def delete_document(doc_id: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ── Chunks ─────────────────────────────────────────────────

async def create_chunk(document_id: str, chunk_index: int, content: str, content_hash: str, token_count: int, embedding: list[float] | None = None) -> dict:
    chunk_id = _new_id()
    db = await get_db()
    try:
        embedding_bytes = None
        if embedding:
            import struct
            embedding_bytes = struct.pack(f"{len(embedding)}f", *embedding)
        await db.execute(
            """INSERT INTO chunks (id, document_id, chunk_index, content, content_hash, token_count, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chunk_id, document_id, chunk_index, content, content_hash, token_count, embedding_bytes),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
        row = await cursor.fetchone()
        return dict(row)
    finally:
        await db.close()


# ── Conversations & Messages ──────────────────────────────

async def create_conversation(title: str = "New conversation", model: str | None = None) -> dict:
    conv_id = _new_id()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO conversations (id, title, model) VALUES (?, ?, ?)",
            (conv_id, title, model),
        )
        await db.commit()
        return {"id": conv_id, "title": title, "model": model, "created_at": _now()}
    finally:
        await db.close()


async def list_conversations(page: int = 1, per_page: int = 50) -> list[dict]:
    db = await get_db()
    try:
        offset = (page - 1) * per_page
        cursor = await db.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def create_message(
    conversation_id: str, role: str, content: str,
    citations: str | None = None, parent_id: str | None = None,
    token_count: int | None = None, generation_ms: int | None = None,
) -> dict:
    msg_id = _new_id()
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO messages (id, conversation_id, role, content, citations, parent_id, token_count, generation_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, conversation_id, role, content, citations, parent_id, token_count, generation_ms),
        )
        await db.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )
        await db.commit()
        return {"id": msg_id, "conversation_id": conversation_id, "role": role, "content": content}
    finally:
        await db.close()


async def get_messages(conversation_id: str, page: int = 1, per_page: int = 100) -> list[dict]:
    db = await get_db()
    try:
        offset = (page - 1) * per_page
        cursor = await db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
            (conversation_id, per_page, offset),
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


# ── Notes ──────────────────────────────────────────────────

async def create_note(title: str, content: str, tags: list[str] | None = None, folder_path: str = "/") -> dict:
    note_id = _new_id()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO notes (id, title, content, tags, folder_path) VALUES (?, ?, ?, ?, ?)",
            (note_id, title, content, json.dumps(tags or []), folder_path),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        return dict(await cursor.fetchone())
    finally:
        await db.close()


async def list_notes(folder: str | None = None, archived: bool = False, page: int = 1, per_page: int = 50) -> list[dict]:
    db = await get_db()
    try:
        where = ["is_archived = ?"]
        params: list[Any] = [1 if archived else 0]
        if folder:
            where.append("folder_path = ?"); params.append(folder)
        offset = (page - 1) * per_page
        cursor = await db.execute(
            f"SELECT * FROM notes WHERE {' AND '.join(where)} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            [*params, per_page, offset],
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def update_note(note_id: str, title: str | None = None, content: str | None = None, tags: list[str] | None = None) -> dict | None:
    db = await get_db()
    try:
        fields = []
        params: list[Any] = []
        if title is not None:
            fields.append("title = ?"); params.append(title)
        if content is not None:
            fields.append("content = ?"); params.append(content)
        if tags is not None:
            fields.append("tags = ?"); params.append(json.dumps(tags))
        if fields:
            params.append(note_id)
            await db.execute(
                f"UPDATE notes SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                params,
            )
            await db.commit()
        cursor = await db.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def delete_note(note_id: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ── Settings ───────────────────────────────────────────────

async def get_settings() -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}
    finally:
        await db.close()


async def update_setting(key: str, value: Any) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
            (key, json.dumps(value)),
        )
        await db.commit()
    finally:
        await db.close()
```

Save `backend/app/storage/file_store.py`:

```python
"""Local filesystem management for uploaded documents."""

from __future__ import annotations

from pathlib import Path
import shutil

from app.config import settings


def get_upload_dir() -> Path:
    path = settings.data_dir / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_file(filename: str, content: bytes) -> Path:
    dest = get_upload_dir() / filename
    dest.write_bytes(content)
    return dest


def read_file(path: str | Path) -> bytes:
    return Path(path).read_bytes()


def delete_file(path: str | Path) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()


def get_disk_usage() -> dict:
    upload_dir = get_upload_dir()
    total = sum(f.stat().st_size for f in upload_dir.rglob("*") if f.is_file())
    return {
        "upload_dir": str(upload_dir),
        "total_bytes": total,
        "total_mb": round(total / (1024 * 1024), 2),
    }
```

- [ ] **Step 1.5: Create core utility modules**

Save `backend/app/core/__init__.py` — empty.

Save `backend/app/core/chunking.py`:

```python
"""Text chunking strategies for document ingestion."""

from __future__ import annotations

import hashlib
from typing import Protocol


class Tokenizer(Protocol):
    def encode(self, text: str) -> list[int]: ...
    def decode(self, tokens: list[int]) -> str: ...


def chunk_by_tokens(
    text: str,
    tokenizer: Tokenizer,
    max_tokens: int = 512,
    overlap: int = 64,
) -> list[dict]:
    """Split text into overlapping token-aligned chunks."""
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        content_hash = hashlib.sha256(chunk_text.encode()).hexdigest()[:16]
        chunks.append({
            "content": chunk_text,
            "token_count": len(chunk_tokens),
            "content_hash": content_hash,
        })
        start += max_tokens - overlap
    return chunks


def chunk_by_characters(
    text: str,
    max_chars: int = 2000,
    overlap: int = 200,
) -> list[dict]:
    """Simple character-based chunking (fallback when no tokenizer)."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk_text = text[start:end]
        content_hash = hashlib.sha256(chunk_text.encode()).hexdigest()[:16]
        chunks.append({
            "content": chunk_text,
            "token_count": len(chunk_text.split()),
            "content_hash": content_hash,
        })
        start += max_chars - overlap
    return chunks
```

Save `backend/app/core/pii.py`:

```python
"""PII detection and redaction using spaCy NER."""

from __future__ import annotations

import re
from typing import Protocol


PII_PATTERNS: list[tuple[str, str, str]] = [
    ("EMAIL", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    ("PHONE", r"\+?1?\d{10,15}"),
    ("SSN", r"\d{3}-\d{2}-\d{4}"),
]


class NERModel(Protocol):
    def __call__(self, text: str) -> list[dict]: ...


def redact_patterns(text: str, replacement: str = "[REDACTED]") -> str:
    """Redact common PII patterns via regex."""
    result = text
    for name, pattern in PII_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


def redact_with_ner(text: str, ner_model: NERModel | None = None) -> tuple[str, list[dict]]:
    """Redact PII using NER model + regex fallback. Returns (redacted_text, detections)."""
    detections: list[dict] = []

    # Regex-based first pass
    for name, pattern in PII_PATTERNS:
        for match in re.finditer(pattern, text):
            detections.append({"type": name, "start": match.start(), "end": match.end(), "text": match.group()})

    # NER-based second pass (if model provided)
    if ner_model is not None:
        for entity in ner_model(text):
            detections.append({"type": entity.get("label", "UNKNOWN"), "start": entity["start"], "end": entity["end"], "text": entity["text"]})

    # Sort by position and redact (reverse order to preserve positions)
    detections.sort(key=lambda d: d["start"], reverse=True)
    result = text
    for d in detections:
        result = result[: d["start"]] + "[REDACTED]" + result[d["end"] :]

    return result, detections
```

- [ ] **Step 1.6: Create model manager stub**

Save `backend/app/models/__init__.py` — empty.

Save `backend/app/models/manager.py`:

```python
"""Model lifecycle manager — singleton with lazy loading and TTL caching."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ModelEntry:
    name: str
    status: str = "unloaded"  # unloaded | loading | ready | error
    loaded_at: datetime | None = None
    memory_mb: float = 0.0
    error: str | None = None


class ModelManager:
    """Singleton model manager. In Phase 1, all models return stub status."""

    _instance: ModelManager | None = None

    def __new__(cls) -> ModelManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models: dict[str, ModelEntry] = {}
            cls._instance._profiles: dict[str, dict] = {}
        return cls._instance

    def register_profile(self, name: str, config: dict) -> None:
        self._profiles[name] = config

    def get_status(self) -> dict[str, Any]:
        return {
            "models": {name: {"status": m.status, "memory_mb": m.memory_mb, "error": m.error} for name, m in self._models.items()},
            "profiles": self._profiles,
            "active_profile": None,
        }

    def get_model(self, name: str) -> ModelEntry | None:
        return self._models.get(name)

    def unload(self, name: str) -> bool:
        if name in self._models:
            self._models[name].status = "unloaded"
            self._models[name].loaded_at = None
            return True
        return False

    async def load_model(self, name: str, model_type: str) -> ModelEntry:
        """Stub: just registers the model as ready."""
        entry = ModelEntry(name=name, status="ready", loaded_at=datetime.now(timezone.utc))
        self._models[name] = entry
        return entry


model_manager = ModelManager()
```

- [ ] **Step 1.7: Create FastAPI app factory**

Save `backend/app/main.py`:

```python
"""Hearth FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.storage.database import init_db, check_db_health
from app.models.manager import model_manager

# API routers will be imported and included in Phase 2
# from app.api import documents, chat, notes, conversations, search, settings, models_api, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup, clean up on shutdown."""
    await init_db()
    for name, cfg in settings.profiles.items():
        model_manager.register_profile(name, cfg)
    yield
    # Graceful shutdown: flush, unload models (stub for now)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Hearth API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoint (always available)
    @app.get("/api/system/health")
    async def health_check():
        db_health = await check_db_health()
        return {
            "status": "ok",
            "version": "0.1.0",
            "database": db_health,
        }

    # Model status endpoint (stub)
    @app.get("/api/models/status")
    async def model_status():
        return model_manager.get_status()

    return app


app = create_app()
```

- [ ] **Step 1.8: Create tests**

Save `backend/tests/__init__.py` — empty.

Save `backend/tests/conftest.py`:

```python
"""Test configuration and fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_text() -> str:
    return (
        "Hearth is a fully offline, local-server-based notes & research assistant. "
        "Users drop in PDFs, photos, or voice memos. "
        "All data stays on the device."
    )


@pytest.fixture
def sample_pii_text() -> str:
    return "Contact john.doe@example.com or call 555-123-4567. SSN: 123-45-6789."
```

Save `backend/tests/test_storage.py`:

```python
"""Tests for storage layer — repository CRUD operations."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_and_get_document():
    from app.storage.repository import create_document, get_document, delete_document

    doc = await create_document(
        title="test.pdf",
        doc_type="pdf",
        mime_type="application/pdf",
        file_path="/tmp/test.pdf",
        file_size=1024,
    )
    assert doc["title"] == "test.pdf"
    assert doc["status"] == "pending"

    fetched = await get_document(doc["id"])
    assert fetched["id"] == doc["id"]

    deleted = await delete_document(doc["id"])
    assert deleted is True


@pytest.mark.asyncio
async def test_create_conversation_and_messages():
    from app.storage.repository import create_conversation, create_message, get_messages

    conv = await create_conversation(title="Test chat")
    assert conv["title"] == "Test chat"

    msg = await create_message(conv["id"], "user", "Hello world")
    assert msg["role"] == "user"

    msgs = await get_messages(conv["id"])
    assert len(msgs) == 1
```

Save `backend/tests/test_core.py`:

```python
"""Tests for core utilities — chunking and PII."""

from __future__ import annotations

from app.core.chunking import chunk_by_characters
from app.core.pii import redact_patterns


def test_chunk_by_characters(sample_text: str):
    chunks = chunk_by_characters(sample_text, max_chars=50, overlap=10)
    assert len(chunks) >= 2
    for c in chunks:
        assert "content" in c
        assert "content_hash" in c
        assert "token_count" in c


def test_redact_patterns(sample_pii_text: str):
    result = redact_patterns(sample_pii_text)
    assert "[REDACTED]" in result
    assert "john.doe@example.com" not in result
```

- [ ] **Step 1.9: Create Dockerfile and gitkeep files**

Save `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8765/api/system/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"]
```

Create empty gitkeep files:
```bash
mkdir -p backend/data backend/models
touch backend/data/.gitkeep backend/models/.gitkeep
```

- [ ] **Step 1.10: Run tests**

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Expected output: all tests pass.

- [ ] **Step 1.11: Start and verify**

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

In another terminal:
```bash
curl http://localhost:8765/api/system/health
```

Expected: `{"status": "ok", "version": "0.1.0", "database": {"status": "ok", "documents": 0, "chunks": 0}}`

- [ ] **Step 1.12: Commit**

```bash
git add backend/
git commit -m "feat: backend foundation - config, DB schema, storage, core utils, app factory"

---

## Task 2: Backend API Skeleton

**Branch:** `feat/backend-api-skeleton` (branches from `feat/backend-foundation`)

**Goal:** All API route modules with proper response stubs, request validation, and error handling. Every endpoint from the spec returns a valid response.

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/documents.py`
- Create: `backend/app/api/chat.py`
- Create: `backend/app/api/notes.py`
- Create: `backend/app/api/conversations.py`
- Create: `backend/app/api/search.py`
- Create: `backend/app/api/settings.py`
- Create: `backend/app/api/models_api.py`
- Create: `backend/app/api/system.py`
- Modify: `backend/app/main.py` (include routers)
- Create: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `app.storage.repository.*` (all CRUD functions), `app.config.settings`, `app.models.manager.model_manager`, `app.storage.file_store.*`
- Produces: Each router module exposes an `APIRouter(prefix=...)` with tagged routes

---

- [ ] **Step 2.1: Create API init and include routers**

Save `backend/app/api/__init__.py`:

```python
"""API route modules. Each submodule exports a router."""
```

Modify `backend/app/main.py` to include all routers. Replace the placeholder comment and add import:

```python
from app.api import documents, chat, notes, conversations, search, settings as settings_router, models_api, system as system_router
```

Add inside `create_app()` before the health endpoint:

```python
    # Include API routers
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(notes.router)
    app.include_router(conversations.router)
    app.include_router(search.router)
    app.include_router(settings_router.router)
    app.include_router(models_api.router)
    app.include_router(system_router.router)
```

Move the health endpoint from main.py to `system.py` and remove the inline definition from main.py.

- [ ] **Step 2.2: Create documents API**

Save `backend/app/api/documents.py`:

```python
"""Document upload, list, delete, reindex endpoints."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.storage.repository import create_document, get_document, list_documents, delete_document, update_document_status
from app.storage.file_store import save_file

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), folder: str = Form("/")):
    content = await file.read()
    file_path = save_file(file.filename or "unnamed", content)
    doc = await create_document(
        title=file.filename or "unnamed",
        doc_type=_infer_type(file.filename or ""),
        mime_type=file.content_type or "application/octet-stream",
        file_path=str(file_path),
        file_size=len(content),
        folder_path=folder,
    )
    return {"id": doc["id"], "title": doc["title"], "status": doc["status"]}


@router.get("")
async def list_docs(
    status: Optional[str] = None,
    doc_type: Optional[str] = None,
    folder: Optional[str] = None,
    page: int = 1,
):
    docs = await list_documents(status=status, doc_type=doc_type, folder=folder, page=page)
    return {"documents": docs, "page": page}


@router.get("/{doc_id}")
async def get_doc(doc_id: str):
    doc = await get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/{doc_id}", status_code=204)
async def delete_doc(doc_id: str):
    deleted = await delete_document(doc_id)
    if not deleted:
        raise HTTPException(404, "Document not found")


@router.post("/{doc_id}/reindex")
async def reindex_doc(doc_id: str):
    doc = await get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    await update_document_status(doc_id, "pending")
    return {"id": doc_id, "status": "pending"}


def _infer_type(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    mapping = {"pdf": "pdf", "png": "image", "jpg": "image", "jpeg": "image", "gif": "image",
               "webp": "image", "mp3": "audio", "wav": "audio", "m4a": "audio", "ogg": "audio",
               "txt": "text", "md": "text", "csv": "text", "json": "text"}
    return mapping.get(ext, "note")
```

- [ ] **Step 2.3: Create chat API**

Save `backend/app/api/chat.py`:

```python
"""Chat and streaming endpoint stubs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage.repository import create_message, get_messages

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    context_docs: list[str] | None = None


@router.post("")
async def chat(request: ChatRequest):
    """Stub: returns a mock SSE-style response as JSON. Real streaming in Phase 3."""
    if not request.conversation_id:
        from app.storage.repository import create_conversation
        conv = await create_conversation(title=request.query[:50])
        request.conversation_id = conv["id"]

    # Store user message
    await create_message(request.conversation_id, "user", request.query)

    # Mock assistant response
    mock_reply = f"I found some information related to your query about '{request.query[:50]}'. This is a stub response — full LLM integration comes in Phase 3."
    msg = await create_message(request.conversation_id, "assistant", mock_reply)

    return {
        "conversation_id": request.conversation_id,
        "message": msg,
        "citations": [],
        "token_count": len(mock_reply.split()),
        "generation_ms": 0,
    }


@router.post("/regenerate")
async def regenerate():
    """Stub for Phase 3."""
    return {"message": "Regeneration not implemented in Phase 1"}


@router.post("/branch")
async def branch():
    """Stub for Phase 3."""
    return {"message": "Conversation branching not implemented in Phase 1"}
```

- [ ] **Step 2.4: Create notes, conversations, search, settings, models, system APIs**

Save `backend/app/api/notes.py`:

```python
"""Notes CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage.repository import create_note, list_notes, get_document, update_note, delete_note

router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteCreate(BaseModel):
    title: str
    content: str = ""
    tags: list[str] = []
    folder_path: str = "/"


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


@router.get("")
async def list_all_notes(folder: str | None = None, archived: bool = False, page: int = 1):
    notes = await list_notes(folder=folder, archived=archived, page=page)
    return {"notes": notes, "page": page}


@router.post("")
async def create(body: NoteCreate):
    note = await create_note(title=body.title, content=body.content, tags=body.tags, folder_path=body.folder_path)
    return note


@router.get("/{note_id}")
async def get(note_id: str):
    note = await get_document(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    return note


@router.put("/{note_id}")
async def update(note_id: str, body: NoteUpdate):
    note = await update_note(note_id, title=body.title, content=body.content, tags=body.tags)
    if not note:
        raise HTTPException(404, "Note not found")
    return note


@router.delete("/{note_id}", status_code=204)
async def delete(note_id: str):
    deleted = await delete_note(note_id)
    if not deleted:
        raise HTTPException(404, "Note not found")
```

Save `backend/app/api/conversations.py`:

```python
"""Conversation CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage.repository import create_conversation, list_conversations, get_messages, create_message as repo_create_message

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = "New conversation"
    model: str | None = None


@router.get("")
async def list_all(page: int = 1):
    convs = await list_conversations(page=page)
    return {"conversations": convs, "page": page}


@router.post("")
async def create(body: ConversationCreate):
    conv = await create_conversation(title=body.title, model=body.model)
    return conv


@router.delete("/{conv_id}", status_code=204)
async def delete(conv_id: str):
    from app.storage.repository import delete_document
    # Conversations are stored in repository; for Phase 1 just hard-delete
    deleted = await delete_document(conv_id)
    if not deleted:
        raise HTTPException(404, "Conversation not found")


@router.get("/{conv_id}/messages")
async def get_conv_messages(conv_id: str, page: int = 1):
    msgs = await get_messages(conv_id, page=page)
    return {"messages": msgs, "page": page}
```

Save `backend/app/api/search.py`:

```python
"""Hybrid search endpoint stub."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search(q: str = "", doc_type: str | None = None, folder: str | None = None, page: int = 1):
    """Stub: returns empty results. Full hybrid search in Phase 3."""
    return {"results": [], "query": q, "page": page, "total": 0}
```

Save `backend/app/api/settings.py`:

```python
"""App settings endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.storage.repository import get_settings as repo_get_settings, update_setting

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    settings: dict[str, Any]


@router.get("")
async def get_settings():
    settings = await repo_get_settings()
    return settings


@router.put("")
async def update_settings(body: SettingsUpdate):
    for key, value in body.settings.items():
        await update_setting(key, value)
    return await repo_get_settings()
```

Save `backend/app/api/models_api.py`:

```python
"""Model management endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.manager import model_manager

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/status")
async def model_status():
    return model_manager.get_status()


@router.get("/profiles")
async def get_profiles():
    return model_manager.get_status()["profiles"]


class ProfileSwitch(BaseModel):
    profile: str


@router.post("/profile")
async def switch_profile(body: ProfileSwitch):
    return {"message": f"Profile switch to '{body.profile}' not implemented in Phase 1", "profile": body.profile}


@router.post("/unload/{name}")
async def unload_model(name: str):
    ok = model_manager.unload(name)
    return {"unloaded": ok}


@router.get("/downloads")
async def list_downloads():
    return {"downloads": []}


@router.post("/download")
async def download_model():
    return {"message": "Download not implemented in Phase 1"}
```

Save `backend/app/api/system.py`:

```python
"""System endpoints — health, backup, logs."""

from __future__ import annotations

from fastapi import APIRouter

from app.storage.database import check_db_health

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health_check():
    db_health = await check_db_health()
    return {
        "status": "ok",
        "version": "0.1.0",
        "database": db_health,
    }


@router.get("/logs")
async def get_logs():
    """Stub: returns empty log list."""
    return {"logs": []}


@router.post("/backup")
async def create_backup():
    """Stub: Phase 5."""
    return {"message": "Backup not implemented in Phase 1"}


@router.post("/restore")
async def restore_backup():
    """Stub: Phase 5."""
    return {"message": "Restore not implemented in Phase 1"}
```

- [ ] **Step 2.5: Create API tests**

Save `backend/tests/test_api.py`:

```python
"""API endpoint tests using FastAPI TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"]["status"] == "ok"


def test_list_documents_empty():
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["documents"] == []


def test_list_notes_empty():
    resp = client.get("/api/notes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["notes"] == []


def test_list_conversations_empty():
    resp = client.get("/api/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversations"] == []


def test_chat_stub():
    resp = client.post("/api/chat", json={"query": "Hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert "conversation_id" in data
    assert "message" in data


def test_model_status():
    resp = client.get("/api/models/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "profiles" in data


def test_document_upload():
    resp = client.post("/api/documents/upload", files={"file": ("test.txt", b"Hello world")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "test.txt"
    assert data["status"] == "pending"


def test_get_nonexistent_document():
    resp = client.get("/api/documents/nonexistent-id")
    assert resp.status_code == 404
```

- [ ] **Step 2.6: Run API tests**

```bash
cd backend
pytest tests/test_api.py -v
```

Expected: all tests pass (health, empty lists, chat stub, model status, upload, 404).

- [ ] **Step 2.7: Commit**

```bash
git add backend/app/api/ backend/tests/test_api.py
git commit -m "feat: backend API skeleton - all route stubs with validation and error handling"
```

---

## Task 3: Frontend Foundation

**Branch:** `feat/frontend-foundation`

**Goal:** React + Vite + TypeScript + Tailwind scaffold, layout shell (Header, Sidebar, MainContent, StatusBar), Zustand stores with TypeScript types, API client, and all component stubs matching the spec's component tree.

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/public/manifest.json`
- Create: `frontend/public/icons/.gitkeep`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/store/chatStore.ts`
- Create: `frontend/src/store/docStore.ts`
- Create: `frontend/src/store/settingsStore.ts`
- Create: `frontend/src/hooks/useChat.ts`
- Create: `frontend/src/hooks/useDocuments.ts`
- Create: `frontend/src/hooks/useNotes.ts`
- Create: `frontend/src/hooks/useSearch.ts`
- Create: `frontend/src/hooks/useSettings.ts`
- Create: `frontend/src/hooks/useKeyboard.ts`
- Create: `frontend/src/utils/format.ts`
- Create: `frontend/src/utils/shortcuts.ts`
- Create: `frontend/src/components/layout/AppLayout.tsx`
- Create: `frontend/src/components/layout/Header.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/StatusBar.tsx`
- Create: `frontend/src/components/chat/ChatView.tsx`
- Create: `frontend/src/components/chat/ChatInput.tsx`
- Create: `frontend/src/components/chat/MessageBubble.tsx`
- Create: `frontend/src/components/chat/StreamingText.tsx`
- Create: `frontend/src/components/chat/CitationModal.tsx`
- Create: `frontend/src/components/documents/DocumentList.tsx`
- Create: `frontend/src/components/documents/DocumentItem.tsx`
- Create: `frontend/src/components/documents/UploadZone.tsx`
- Create: `frontend/src/components/documents/DocumentPreview.tsx`
- Create: `frontend/src/components/notes/NoteEditor.tsx`
- Create: `frontend/src/components/notes/NoteList.tsx`
- Create: `frontend/src/components/settings/SettingsPanel.tsx`
- Create: `frontend/src/components/settings/ModelManager.tsx`
- Create: `frontend/src/components/settings/ModelProfileCard.tsx`
- Create: `frontend/src/components/settings/TraceInspector.tsx`
- Create: `frontend/src/components/search/SearchDialog.tsx`
- Create: `frontend/src/components/search/SearchResults.tsx`
- Create: `frontend/src/components/common/Button.tsx`
- Create: `frontend/src/components/common/Modal.tsx`
- Create: `frontend/src/components/common/Toast.tsx`
- Create: `frontend/src/components/common/Spinner.tsx`
- Create: `frontend/src/components/common/ProgressBar.tsx`
- Create: `frontend/src/components/common/EmptyState.tsx`
- Create: `frontend/Dockerfile`

**Interfaces (shared contract between frontend and backend):**
- API base URL: `http://localhost:8765` (proxied via Vite in dev)
- API types defined in `src/api/types.ts` match backend response shapes
- Zustand stores mirror the spec's `ChatStore`, `DocStore`, `SettingsStore` interfaces
- All components render all states: loading, empty, error, data

---

- [ ] **Step 3.1: Scaffold project config files**

Save `frontend/package.json`:

```json
{
  "name": "hearth-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0"
  }
}
```

Save `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"]
}
```

Save `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

Save `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
    },
  },
});
```

Save `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'media',
  theme: {
    extend: {
      colors: {
        hearth: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          300: '#9fb3c8',
          400: '#829ab1',
          500: '#627d98',
          600: '#486581',
          700: '#334e68',
          800: '#243b53',
          900: '#102a43',
        },
      },
    },
  },
  plugins: [],
};
```

Save `frontend/postcss.config.js`:

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

Save `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Hearth — Fully Offline Notes & Research Assistant" />
    <link rel="manifest" href="/manifest.json" />
    <title>Hearth</title>
  </head>
  <body class="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Save `frontend/public/manifest.json`:

```json
{
  "name": "Hearth",
  "short_name": "Hearth",
  "description": "Fully offline notes & research assistant",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#f0f4f8",
  "theme_color": "#243b53",
  "icons": []
}
```

- [ ] **Step 3.2: TypeScript types**

Save `frontend/src/vite-env.d.ts`:

```typescript
/// <reference types="vite/client" />
```

Save `frontend/src/types/index.ts`:

```typescript
// ── Documents ──────────────────────────────────────────────

export type DocType = 'pdf' | 'image' | 'audio' | 'note' | 'text';
export type DocStatus = 'pending' | 'processing' | 'ready' | 'error';

export interface Document {
  id: string;
  title: string;
  doc_type: DocType;
  mime_type: string;
  file_path: string;
  file_size: number;
  status: DocStatus;
  error_msg: string | null;
  source_info: string | null;
  folder_path: string;
  tags: string[];
  checksum: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

// ── Chunks ─────────────────────────────────────────────────

export interface Chunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  content_hash: string;
  token_count: number;
  created_at: string;
}

// ── Conversations & Messages ──────────────────────────────

export interface Conversation {
  id: string;
  title: string;
  model: string | null;
  context_docs: string[];
  created_at: string;
  updated_at: string;
}

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  citations: string | null;
  pii_redacted: boolean;
  parent_id: string | null;
  token_count: number | null;
  generation_ms: number | null;
  created_at: string;
}

// ── Notes ──────────────────────────────────────────────────

export interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  folder_path: string;
  is_pinned: boolean;
  is_archived: boolean;
  checksum: string | null;
  created_at: string;
  updated_at: string;
}

// ── Citations ──────────────────────────────────────────────

export interface Citation {
  id: string;
  doc_title: string;
  text: string;
  score: number;
  verified: boolean;
  color: 'green' | 'amber' | 'red';
}

// ── Chat ───────────────────────────────────────────────────

export interface ChatRequest {
  query: string;
  conversation_id?: string;
  context_docs?: string[];
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  citations: Citation[];
  token_count: number;
  generation_ms: number;
}

// ── Settings ───────────────────────────────────────────────

export interface AppSettings {
  [key: string]: unknown;
}

export interface ModelStatus {
  models: Record<string, { status: string; memory_mb: number; error: string | null }>;
  profiles: Record<string, unknown>;
  active_profile: string | null;
}

// ── SSE Events ─────────────────────────────────────────────

export type SSEEventType = 'status' | 'token' | 'done' | 'error';

export interface SSEEvent {
  event: SSEEventType;
  data: unknown;
}

export interface StatusEvent {
  status: string;
  documents?: number;
}

export interface TokenEvent {
  token: string;
}

export interface DoneEvent {
  citations: Citation[];
  token_count: number;
  generation_ms: number;
  conversation_id: string;
}

export interface ErrorEvent {
  message: string;
  code: string;
}
```

- [ ] **Step 3.3: API client**

Save `frontend/src/api/types.ts`:

```typescript
/** Re-export for convenience. */
export type {
  Document,
  Chunk,
  Conversation,
  Message,
  Note,
  Citation,
  ChatRequest,
  ChatResponse,
  AppSettings,
  ModelStatus,
  SSEMessage,
} from '../types';
```

Save `frontend/src/api/client.ts`:

```typescript
import type {
  Document,
  Conversation,
  Message,
  Note,
  ChatRequest,
  ChatResponse,
  AppSettings,
  ModelStatus,
} from '../types';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Documents ──────────────────────────────────────────────

export const documents = {
  list: (params?: Record<string, string>) =>
    request<{ documents: Document[]; page: number }>(
      `/documents?${new URLSearchParams(params)}`
    ),
  get: (id: string) => request<Document>(`/documents/${id}`),
  upload: async (file: File, folder?: string) => {
    const form = new FormData();
    form.append('file', file);
    if (folder) form.append('folder', folder);
    const res = await fetch(`${BASE}/documents/upload`, { method: 'POST', body: form });
    return res.json() as Promise<{ id: string; title: string; status: string }>;
  },
  delete: (id: string) => request<void>(`/documents/${id}`, { method: 'DELETE' }),
  reindex: (id: string) => request<{ id: string; status: string }>(`/documents/${id}/reindex`, { method: 'POST' }),
};

// ── Conversations ──────────────────────────────────────────

export const conversations = {
  list: (page = 1) => request<{ conversations: Conversation[]; page: number }>(`/conversations?page=${page}`),
  create: (title?: string) =>
    request<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify({ title: title || 'New conversation' }),
    }),
  delete: (id: string) => request<void>(`/conversations/${id}`, { method: 'DELETE' }),
  messages: (id: string, page = 1) =>
    request<{ messages: Message[]; page: number }>(`/conversations/${id}/messages?page=${page}`),
};

// ── Chat ───────────────────────────────────────────────────

export const chat = {
  send: (req: ChatRequest) =>
    request<ChatResponse>('/chat', { method: 'POST', body: JSON.stringify(req) }),
};

// ── Notes ──────────────────────────────────────────────────

export const notes = {
  list: (params?: Record<string, string>) =>
    request<{ notes: Note[]; page: number }>(`/notes?${new URLSearchParams(params)}`),
  create: (data: { title: string; content?: string; tags?: string[]; folder_path?: string }) =>
    request<Note>('/notes', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: string) => request<Note>(`/notes/${id}`),
  update: (id: string, data: Partial<Note>) =>
    request<Note>(`/notes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => request<void>(`/notes/${id}`, { method: 'DELETE' }),
};

// ── Settings ───────────────────────────────────────────────

export const settings = {
  get: () => request<AppSettings>('/settings'),
  update: (data: Record<string, unknown>) =>
    request<AppSettings>('/settings', { method: 'PUT', body: JSON.stringify({ settings: data }) }),
};

// ── Models ─────────────────────────────────────────────────

export const models = {
  status: () => request<ModelStatus>('/models/status'),
  profiles: () => request<Record<string, unknown>>('/models/profiles'),
  unload: (name: string) => request<{ unloaded: boolean }>(`/models/unload/${name}`, { method: 'POST' }),
};
```

- [ ] **Step 3.4: Zustand stores**

Save `frontend/src/store/chatStore.ts`:

```typescript
import { create } from 'zustand';
import type { Conversation, Message, Citation } from '../types';
import * as api from '../api/client';

interface ChatStore {
  conversations: Conversation[];
  activeConversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  streamBuffer: string;
  statusMessage: string | null;
  error: string | null;

  sendMessage: (query: string) => Promise<void>;
  regenerate: () => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  clearConversation: () => Promise<void>;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  isStreaming: false,
  streamBuffer: '',
  statusMessage: null,
  error: null,

  sendMessage: async (query: string) => {
    set({ isStreaming: true, statusMessage: 'Sending...', error: null, streamBuffer: '' });
    try {
      const resp = await api.chat.send({ query, conversation_id: get().activeConversationId ?? undefined });
      set((s) => ({
        conversations: s.conversations.some((c) => c.id === resp.conversation_id)
          ? s.conversations
          : [...s.conversations, { id: resp.conversation_id, title: query.slice(0, 50), model: null, context_docs: [], created_at: '', updated_at: '' }],
        activeConversationId: resp.conversation_id,
        messages: [...s.messages, resp.message],
        isStreaming: false,
        statusMessage: null,
      }));
    } catch (e: unknown) {
      set({ isStreaming: false, error: (e as Error).message, statusMessage: null });
    }
  },

  regenerate: async () => { /* Phase 3 */ },
  selectConversation: async (id: string) => {
    set({ activeConversationId: id, messages: [] });
    try {
      const resp = await api.conversations.messages(id);
      set({ messages: resp.messages });
    } catch { /* ignore */ }
  },
  clearConversation: () => set({ activeConversationId: null, messages: [], streamBuffer: '' }),
}));
```

Save `frontend/src/store/docStore.ts`:

```typescript
import { create } from 'zustand';
import type { Document } from '../types';
import * as api from '../api/client';

interface DocStore {
  documents: Document[];
  selectedDoc: Document | null;
  uploadProgress: Record<string, number>;
  isUploading: boolean;

  fetchDocuments: () => Promise<void>;
  uploadFiles: (files: File[]) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  reindexDocument: (id: string) => Promise<void>;
  selectDocument: (doc: Document | null) => void;
}

export const useDocStore = create<DocStore>((set) => ({
  documents: [],
  selectedDoc: null,
  uploadProgress: {},
  isUploading: false,

  fetchDocuments: async () => {
    try {
      const resp = await api.documents.list();
      set({ documents: resp.documents });
    } catch { /* ignore */ }
  },

  uploadFiles: async (files: File[]) => {
    set({ isUploading: true });
    for (const file of files) {
      try {
        await api.documents.upload(file);
      } catch { /* ignore */ }
    }
    set({ isUploading: false });
    // Re-fetch document list
    const resp = await api.documents.list();
    set({ documents: resp.documents });
  },

  deleteDocument: async (id: string) => {
    await api.documents.delete(id);
    set((s) => ({ documents: s.documents.filter((d) => d.id !== id) }));
  },

  reindexDocument: async (id: string) => {
    await api.documents.reindex(id);
  },

  selectDocument: (doc) => set({ selectedDoc: doc }),
}));
```

Save `frontend/src/store/settingsStore.ts`:

```typescript
import { create } from 'zustand';
import type { AppSettings, ModelStatus } from '../types';
import * as api from '../api/client';

interface SettingsStore {
  settings: AppSettings;
  modelStatus: ModelStatus | null;
  isLoading: boolean;

  fetchSettings: () => Promise<void>;
  fetchModelStatus: () => Promise<void>;
  updateSettings: (partial: Partial<AppSettings>) => Promise<void>;
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: {},
  modelStatus: null,
  isLoading: false,

  fetchSettings: async () => {
    try {
      const s = await api.settings.get();
      set({ settings: s });
    } catch { /* ignore */ }
  },

  fetchModelStatus: async () => {
    try {
      const s = await api.models.status();
      set({ modelStatus: s });
    } catch { /* ignore */ }
  },

  updateSettings: async (partial) => {
    set({ isLoading: true });
    try {
      await api.settings.update(partial);
      set((s) => ({ settings: { ...s.settings, ...partial }, isLoading: false }));
    } catch {
      set({ isLoading: false });
    }
  },
}));
```

- [ ] **Step 3.5: Utility modules**

Save `frontend/src/utils/format.ts`:

```typescript
/** Format file size in human-readable form. */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Format date to locale string. */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Truncate text with ellipsis. */
export function truncate(text: string, max = 100): string {
  return text.length > max ? text.slice(0, max) + '…' : text;
}
```

Save `frontend/src/utils/shortcuts.ts`:

```typescript
/** Keyboard shortcut handler type. */
export type ShortcutAction =
  | { action: 'search' }
  | { action: 'new-note' }
  | { action: 'send-message' }
  | { action: 'clear-chat' }
  | { action: 'open-settings' }
  | { action: 'close-panel' }
  | { action: 'upload-file' }
  | { action: 'toggle-pii' };

type ShortcutCallback = (act: ShortcutAction) => void;

export function handleKeyDown(e: KeyboardEvent, cb: ShortcutCallback): void {
  const ctrl = e.ctrlKey || e.metaKey;
  const shift = e.shiftKey;

  if (ctrl && e.key === 'k') { e.preventDefault(); cb({ action: 'search' }); }
  if (ctrl && !shift && e.key === 'n') { e.preventDefault(); cb({ action: 'new-note' }); }
  if (ctrl && e.key === 'Enter') { e.preventDefault(); cb({ action: 'send-message' }); }
  if (ctrl && shift && e.key === 'C') { e.preventDefault(); cb({ action: 'clear-chat' }); }
  if (ctrl && e.key === ',') { e.preventDefault(); cb({ action: 'open-settings' }); }
  if (e.key === 'Escape') { e.preventDefault(); cb({ action: 'close-panel' }); }
  if (ctrl && shift && e.key === 'U') { e.preventDefault(); cb({ action: 'upload-file' }); }
  if (ctrl && shift && e.key === 'P') { e.preventDefault(); cb({ action: 'toggle-pii' }); }
}

/** Register global keyboard listener. Returns cleanup function. */
export function registerShortcuts(cb: ShortcutCallback): () => void {
  const handler = (e: KeyboardEvent) => handleKeyDown(e, cb);
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}
```

- [ ] **Step 3.6: React hooks**

Save `frontend/src/hooks/useChat.ts`:

```typescript
import { useChatStore } from '../store/chatStore';

export function useChat() {
  return useChatStore();
}
```

Save `frontend/src/hooks/useDocuments.ts`:

```typescript
import { useEffect } from 'react';
import { useDocStore } from '../store/docStore';

export function useDocuments() {
  const store = useDocStore();
  useEffect(() => { store.fetchDocuments(); }, []);
  return store;
}
```

Save `frontend/src/hooks/useNotes.ts` — empty hook stub:

```typescript
export function useNotes() {
  return { notes: [], isLoading: false };
}
```

Save `frontend/src/hooks/useSearch.ts` — empty hook stub:

```typescript
export function useSearch() {
  return { results: [], query: '', isOpen: false, open: () => {}, close: () => {}, search: () => {} };
}
```

Save `frontend/src/hooks/useSettings.ts`:

```typescript
import { useEffect } from 'react';
import { useSettingsStore } from '../store/settingsStore';

export function useSettings() {
  const store = useSettingsStore();
  useEffect(() => { store.fetchSettings(); store.fetchModelStatus(); }, []);
  return store;
}
```

Save `frontend/src/hooks/useKeyboard.ts`:

```typescript
import { useEffect, useCallback } from 'react';
import { registerShortcuts, type ShortcutAction } from '../utils/shortcuts';

type ActionHandler = (action: ShortcutAction) => void;

export function useKeyboard(handler: ActionHandler) {
  const stableHandler = useCallback(handler, [handler]);
  useEffect(() => registerShortcuts(stableHandler), [stableHandler]);
}
```

- [ ] **Step 3.7: Layout components**

Save `frontend/src/components/layout/AppLayout.tsx`:

```tsx
import type { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { StatusBar } from './StatusBar';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex flex-col h-screen">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
          {children}
        </main>
      </div>
      <StatusBar />
    </div>
  );
}
```

Save `frontend/src/components/layout/Header.tsx`:

```tsx
import { useState } from 'react';

export function Header() {
  const [piiEnabled, setPiiEnabled] = useState(false);

  return (
    <header className="flex items-center justify-between px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2">
        <span className="text-xl">🔥</span>
        <h1 className="text-lg font-semibold">Hearth</h1>
      </div>

      <div className="flex items-center gap-3">
        <button
          className="px-3 py-1 text-sm rounded-md bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
          onClick={() => {}}
          title="Search (Ctrl+K)"
        >
          🔍 Search
        </button>

        <button
          className={`px-3 py-1 text-sm rounded-md ${
            piiEnabled
              ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
              : 'bg-gray-100 dark:bg-gray-700'
          }`}
          onClick={() => setPiiEnabled(!piiEnabled)}
          title="Toggle PII redaction (Ctrl+Shift+P)"
          aria-label="Toggle PII redaction"
          aria-pressed={piiEnabled}
        >
          🛡️ PII {piiEnabled ? 'ON' : 'OFF'}
        </button>

        <button
          className="px-3 py-1 text-sm rounded-md bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
          onClick={() => {}}
          title="Settings (Ctrl+,)"
        >
          ⚙️
        </button>
      </div>
    </header>
  );
}
```

Save `frontend/src/components/layout/Sidebar.tsx`:

```tsx
export function Sidebar() {
  return (
    <aside className="w-64 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col overflow-y-auto">
      {/* Documents section */}
      <div className="p-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">Documents</h2>
        <div className="space-y-1">
          <div className="text-sm text-gray-400 italic px-2 py-1">No documents yet</div>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-gray-200 dark:border-gray-700" />

      {/* Notes section */}
      <div className="p-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">Notes</h2>
        <div className="space-y-1">
          <div className="text-sm text-gray-400 italic px-2 py-1">No notes yet</div>
        </div>
      </div>

      {/* Chats section */}
      <div className="p-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">Chats</h2>
        <div className="space-y-1">
          <div className="text-sm text-gray-400 italic px-2 py-1">No conversations yet</div>
        </div>
      </div>
    </aside>
  );
}
```

Save `frontend/src/components/layout/StatusBar.tsx`:

```tsx
import { useSettingsStore } from '../../store/settingsStore';

export function StatusBar() {
  const modelStatus = useSettingsStore((s) => s.modelStatus);

  return (
    <footer className="flex items-center justify-between px-4 py-1.5 text-xs bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 text-gray-500">
      <div className="flex items-center gap-3">
        <span>◉ {modelStatus?.active_profile ?? 'No model loaded'}</span>
      </div>
      <div className="flex items-center gap-3">
        <span>🖥 Memory —</span>
      </div>
    </footer>
  );
}
```

- [ ] **Step 3.8: Chat components (stubs)**

Save `frontend/src/components/chat/ChatView.tsx`:

```tsx
import { useChatStore } from '../../store/chatStore';
import { ChatInput } from './ChatInput';
import { MessageBubble } from './MessageBubble';
import { EmptyState } from '../common/EmptyState';

export function ChatView() {
  const { messages, isStreaming, streamBuffer, error } = useChatStore();

  if (messages.length === 0 && !isStreaming && !error) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 flex items-center justify-center">
          <EmptyState
            icon="💬"
            title="Start a conversation"
            description="Upload a document and ask questions about it, or just type a message."
          />
        </div>
        <ChatInput />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && streamBuffer && (
          <div className="text-sm text-gray-500 italic">▌{streamBuffer}</div>
        )}
        {error && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
            Error: {error}
          </div>
        )}
      </div>
      <ChatInput />
    </div>
  );
}
```

Save `frontend/src/components/chat/ChatInput.tsx`:

```tsx
import { useState, useRef } from 'react';
import { useChatStore } from '../../store/chatStore';

export function ChatInput() {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  const handleSubmit = () => {
    const query = input.trim();
    if (!query || isStreaming) return;
    sendMessage(query);
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-4 border-t border-gray-200 dark:border-gray-700">
      <div className="flex items-end gap-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-2">
        <button className="p-2 text-gray-400 hover:text-gray-600" title="Attach file (Ctrl+Shift+U)">📎</button>
        <button className="p-2 text-gray-400 hover:text-gray-600" title="Voice input">🎤</button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question... (Ctrl+Enter to send)"
          className="flex-1 resize-none bg-transparent outline-none text-sm py-1.5 max-h-32"
          rows={1}
          disabled={isStreaming}
          aria-label="Chat input"
        />

        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isStreaming}
          className="px-4 py-1.5 bg-hearth-600 text-white rounded-md text-sm hover:bg-hearth-700 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Send message"
        >
          ➤
        </button>
      </div>
    </div>
  );
}
```

Save `frontend/src/components/chat/MessageBubble.tsx`:

```tsx
import type { Message } from '../../types';

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-hearth-600 text-white'
            : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {message.citations && (
          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
            <span className="text-xs text-gray-400">Citations available</span>
          </div>
        )}
      </div>
    </div>
  );
}
```

Save `frontend/src/components/chat/StreamingText.tsx` — minimal:

```tsx
interface Props {
  text: string;
}

export function StreamingText({ text }: Props) {
  return <span>{text}</span>;
}
```

Save `frontend/src/components/chat/CitationModal.tsx` — minimal:

```tsx
export function CitationModal() {
  return null; // Phase 4
}
```

- [ ] **Step 3.9: Common components**

Save `frontend/src/components/common/Button.tsx`:

```tsx
import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  children: ReactNode;
}

export function Button({ variant = 'primary', children, className = '', ...props }: Props) {
  const base = 'px-4 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
  const variants = {
    primary: 'bg-hearth-600 text-white hover:bg-hearth-700',
    secondary: 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600',
    ghost: 'hover:bg-gray-100 dark:hover:bg-gray-800',
  };
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
```

Save `frontend/src/components/common/Modal.tsx`:

```tsx
import { useEffect, type ReactNode } from 'react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: Props) {
  useEffect(() => {
    if (isOpen) {
      const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
      window.addEventListener('keydown', handler);
      return () => window.removeEventListener('keydown', handler);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose} role="dialog" aria-modal="true" aria-label={title}>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Close">✕</button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
```

Save `frontend/src/components/common/Toast.tsx`:

```tsx
import { useState, useEffect } from 'react';

interface Props {
  message: string;
  type?: 'info' | 'error' | 'success';
  duration?: number;
  onClose: () => void;
}

export function Toast({ message, type = 'info', duration = 4000, onClose }: Props) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => { setVisible(false); onClose(); }, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  if (!visible) return null;

  const colors = {
    info: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800',
    error: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-200 dark:border-red-800',
    success: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-200 dark:border-green-800',
  };

  return (
    <div className={`fixed bottom-4 right-4 z-50 px-4 py-2 rounded-lg border shadow-lg text-sm ${colors[type]}`} role="alert">
      {message}
    </div>
  );
}
```

Save `frontend/src/components/common/Spinner.tsx`:

```tsx
interface Props {
  size?: 'sm' | 'md' | 'lg';
}

export function Spinner({ size = 'md' }: Props) {
  const sizes = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' };
  return (
    <div className={`${sizes[size]} animate-spin rounded-full border-2 border-gray-300 border-t-hearth-600`} role="status" aria-label="Loading" />
  );
}
```

Save `frontend/src/components/common/ProgressBar.tsx`:

```tsx
interface Props {
  value: number; // 0-100
  label?: string;
}

export function ProgressBar({ value, label }: Props) {
  return (
    <div className="w-full">
      {label && <div className="text-xs text-gray-500 mb-1">{label}</div>}
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-hearth-600 rounded-full transition-all duration-300"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
```

Save `frontend/src/components/common/EmptyState.tsx`:

```tsx
interface Props {
  icon?: string;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8">
      {icon && <div className="text-4xl mb-4">{icon}</div>}
      <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">{title}</h3>
      {description && <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mb-4">{description}</p>}
      {action && (
        <button onClick={action.onClick} className="px-4 py-2 bg-hearth-600 text-white rounded-md text-sm hover:bg-hearth-700">
          {action.label}
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 3.10: Document, Note, Settings, Search components (minimal stubs)**

Save `frontend/src/components/documents/DocumentList.tsx`:

```tsx
import { useDocuments } from '../../hooks/useDocuments';
import { DocumentItem } from './DocumentItem';
import { EmptyState } from '../common/EmptyState';

export function DocumentList() {
  const { documents, uploadFiles, isUploading } = useDocuments();

  if (documents.length === 0) {
    return (
      <EmptyState
        icon="📄"
        title="No documents yet"
        description="Upload a PDF, image, audio file, or text document to get started."
        action={{ label: 'Upload', onClick: () => document.getElementById('file-upload')?.click() }}
      />
    );
  }

  return (
    <div className="space-y-1">
      {documents.map((doc) => (
        <DocumentItem key={doc.id} document={doc} />
      ))}
    </div>
  );
}
```

Save `frontend/src/components/documents/DocumentItem.tsx`:

```tsx
import type { Document } from '../../types';
import { formatFileSize, formatDate } from '../../utils/format';

interface Props {
  document: Document;
}

export function DocumentItem({ document }: Props) {
  return (
    <div className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer">
      <div className="text-lg">{getIcon(document.doc_type)}</div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{document.title}</div>
        <div className="text-xs text-gray-500">{formatFileSize(document.file_size)} · {formatDate(document.created_at)}</div>
      </div>
      <div className={`text-xs px-2 py-0.5 rounded-full ${statusBadge(document.status)}`}>{document.status}</div>
    </div>
  );
}

function getIcon(type: string): string {
  const icons: Record<string, string> = { pdf: '📕', image: '🖼️', audio: '🎵', note: '📝', text: '📄' };
  return icons[type] || '📄';
}

function statusBadge(status: string): string {
  const colors: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
    processing: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300',
    ready: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300',
    error: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300',
  };
  return colors[status] || colors.pending;
}
```

Save `frontend/src/components/documents/UploadZone.tsx` — drop zone stub:

```tsx
import { useState, useRef } from 'react';
import { useDocStore } from '../../store/docStore';

export function UploadZone() {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadFiles = useDocStore((s) => s.uploadFiles);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length > 0) uploadFiles(Array.from(e.dataTransfer.files));
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        dragging ? 'border-hearth-500 bg-hearth-50 dark:bg-hearth-900/20' : 'border-gray-300 dark:border-gray-600'
      }`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      aria-label="Upload files"
    >
      <div className="text-3xl mb-2">📤</div>
      <p className="text-sm text-gray-500 dark:text-gray-400">Drop files here or click to upload</p>
      <p className="text-xs text-gray-400 mt-1">PDF, images, audio, text files</p>
      <input ref={inputRef} type="file" multiple className="hidden" onChange={(e) => e.target.files && uploadFiles(Array.from(e.target.files))} />
    </div>
  );
}
```

Save `frontend/src/components/documents/DocumentPreview.tsx` — empty stub:

```tsx
export function DocumentPreview() {
  return <div className="p-4 text-sm text-gray-400">Preview not available in Phase 1</div>;
}
```

Save `frontend/src/components/notes/NoteEditor.tsx`:

```tsx
import { useState } from 'react';

export function NoteEditor() {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  return (
    <div className="flex flex-col h-full p-4">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Note title..."
        className="text-xl font-semibold bg-transparent outline-none mb-4 placeholder-gray-400"
        aria-label="Note title"
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Start writing..."
        className="flex-1 bg-transparent outline-none resize-none text-sm placeholder-gray-400"
        aria-label="Note content"
      />
    </div>
  );
}
```

Save `frontend/src/components/notes/NoteList.tsx`:

```tsx
import { EmptyState } from '../common/EmptyState';

export function NoteList() {
  return (
    <EmptyState icon="📝" title="No notes yet" description="Create your first note with Ctrl+N" />
  );
}
```

Save `frontend/src/components/settings/SettingsPanel.tsx`:

```tsx
interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: Props) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-40 flex">
      <div className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 ml-auto overflow-y-auto shadow-xl" role="dialog" aria-label="Settings">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Close settings">✕</button>
        </div>
        <div className="p-4 space-y-6">
          <div>
            <h3 className="text-sm font-medium mb-2">General</h3>
            <p className="text-xs text-gray-400">Settings panel — Phase 4</p>
          </div>
          <div>
            <h3 className="text-sm font-medium mb-2">Models</h3>
            <p className="text-xs text-gray-400">Model management — Phase 4</p>
          </div>
          <div>
            <h3 className="text-sm font-medium mb-2">Traces</h3>
            <p className="text-xs text-gray-400">Pipeline trace inspector — Phase 4</p>
          </div>
        </div>
      </div>
      <div className="flex-1" onClick={onClose} />
    </div>
  );
}
```

Save `frontend/src/components/settings/ModelManager.tsx` — stub:

```tsx
export function ModelManager() {
  return <div className="text-sm text-gray-400">Model management — Phase 4</div>;
}
```

Save `frontend/src/components/settings/ModelProfileCard.tsx` — stub:

```tsx
export function ModelProfileCard() {
  return <div className="text-sm text-gray-400">Profile card — Phase 4</div>;
}
```

Save `frontend/src/components/settings/TraceInspector.tsx` — stub:

```tsx
export function TraceInspector() {
  return <div className="text-sm text-gray-400">Trace inspector — Phase 4</div>;
}
```

Save `frontend/src/components/search/SearchDialog.tsx`:

```tsx
import { useState } from 'react';
import { SearchResults } from './SearchResults';
import type { Document } from '../../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchDialog({ isOpen, onClose }: Props) {
  const [query, setQuery] = useState('');
  const [results] = useState<Document[]>([]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" onClick={onClose} role="dialog" aria-label="Search">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search documents, notes, conversations..."
            className="w-full bg-transparent outline-none text-sm"
            autoFocus
            aria-label="Search query"
          />
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {query ? <SearchResults results={results} query={query} /> : <div className="text-sm text-gray-400 p-2">Type to search...</div>}
        </div>
      </div>
    </div>
  );
}
```

Save `frontend/src/components/search/SearchResults.tsx`:

```tsx
import type { Document } from '../../types';
import { EmptyState } from '../common/EmptyState';

interface Props {
  results: Document[];
  query: string;
}

export function SearchResults({ results, query }: Props) {
  if (results.length === 0) {
    return <EmptyState icon="🔍" title="No results" description={`No results found for "${query}"`} />;
  }
  return (
    <div className="space-y-1">
      {results.map((r) => (
        <div key={r.id} className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer text-sm">{r.title}</div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3.11: App.tsx and main.tsx**

Save `frontend/src/App.tsx`:

```tsx
import { useState, useCallback } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { ChatView } from './components/chat/ChatView';
import { SettingsPanel } from './components/settings/SettingsPanel';
import { SearchDialog } from './components/search/SearchDialog';
import { useKeyboard } from './hooks/useKeyboard';
import type { ShortcutAction } from './utils/shortcuts';

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const handleShortcut = useCallback((action: ShortcutAction) => {
    switch (action.action) {
      case 'search': setSearchOpen((p) => !p); break;
      case 'open-settings': setSettingsOpen((p) => !p); break;
      case 'close-panel':
        setSettingsOpen(false);
        setSearchOpen(false);
        break;
      default: break;
    }
  }, []);

  useKeyboard(handleShortcut);

  return (
    <>
      <AppLayout>
        <ChatView />
      </AppLayout>
      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <SearchDialog isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
```

Save `frontend/src/main.tsx`:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Also create `frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
.dark ::-webkit-scrollbar-thumb { background: #475569; }
```

- [ ] **Step 3.12: Dockerfile**

Save `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 3.13: Install and verify build**

```bash
cd frontend
npm install
npm run typecheck
npm run build
```

Expected: TypeScript check passes, build succeeds, output in `frontend/dist/`.

- [ ] **Step 3.14: Start dev server**

```bash
cd frontend
npm run dev
```

Open browser to `http://localhost:5173`. Expected: Layout renders (header, sidebar, main content with empty chat state, status bar).

- [ ] **Step 3.15: Commit**

```bash
git add frontend/
git commit -m "feat: frontend foundation - Vite scaffold, layout shell, Zustand stores, API client, component stubs"
```

```

