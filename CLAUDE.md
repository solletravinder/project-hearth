# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**All from `hearth/` root:**
```bash
python -m venv .venv && .venv\Scripts\activate   # Windows venv
pip install -e ".[dev]"                           # install with test/lint deps

# Start server (builds React + runs uvicorn)
.\scripts\start.ps1                                # Windows
./scripts/start.sh                                 # Linux/macOS

# Dev mode (React HMR + uvicorn concurrently)
.\scripts\dev.ps1                                  # Windows
./scripts/dev.sh                                   # Linux/macOS

# Or manually:
uvicorn app.main:app --reload --port 8765          # backend only
pytest tests/ -v                                   # run tests
pytest tests/test_api.py -v -k "test_name"         # single test file
ruff check .                                        # lint
ruff check . --fix                                  # lint + fix
mypy app/                                           # type check
```

**Frontend** (from `hearth/static/frontend/`):
```bash
npm install
npm run dev        # Vite dev server on :5173 (proxies /api → :8765)
npm run build      # tsc + vite build → static/frontend/dist/
npm run lint       # ESLint
npm run typecheck  # TypeScript strict mode
```

## Architecture

Hearth is a fully-offline, on-device AI notes & research assistant. Backend (FastAPI + SQLite) serves a React SPA and ML pipelines; frontend is a small 3-route app (Chat, Documents, Notes).

### Backend layers

- **`app/api/`** — REST routers, one per domain (chat, documents, notes, conversations, search, settings, models, system). Each router calls a service function.
- **`app/services/`** — thin service layer between routers and storage/repos. Handles business logic (e.g. triggering ingestion, PII redaction).
- **`app/storage/`** — data access. `schema.py` holds all DDL. `database.py` manages aiosqlite connections with a semaphore (max 10 concurrent). `repos/` has one file per entity (documents, chunks, conversations, messages, notes, settings) exporting CRUD functions. `repository.py` re-exports everything.
- **`app/pipeline/`** — LangGraph state machine for document ingestion. `orchestrator.py` is the entry point called from the documents service; `ingest_workflow.py` builds the graph: classify → extract → chunk → embed → store, with error edges at each step.
- **`app/providers/`** — pluggable model provider abstraction. `base.py` defines `EmbeddingProvider`, `ChatProvider`, `TranscriptionProvider`, `OCRProvider` protocols. `registry.py` (`ProviderRegistry`) selects the active provider based on settings, with fallback chain: remote (Ollama/OpenAI-compat) → local → mock. Implementations: `ollama.py`, `openai_compat.py`. Local models (embedding, whisper, trocr, ner) live in `app/models/` as singleton services.
- **`app/config.py`** — pydantic-settings `Settings` class, env-prefixed `HEARTH_`. Key fields: `chat_provider`, `embedding_provider`, `default_model`, `active_profile` (chunk sizes), `frontend_dist_dir` (points to `static/frontend/dist`). All settings also mirrored in the `settings` SQLite table for runtime changes.
- **`app/main.py`** — application factory. Includes routers, CORS, and SPA serving: mounts `/assets` as StaticFiles from the React build output, uses Jinja2Templates for SPA fallback so React Router works.

### Frontend structure (in `static/frontend/`)

- **`src/api/client.ts`** — single fetch wrapper (`request()`) with `ApiError`. All API modules (documents, conversations, chat, notes, settings, models, search) use it. Base URL is relative (`/api`), proxied by Vite in dev.
- **`src/store/`** — Zustand stores: `chatStore` (conversations, messages, streaming), `docStore`, `settingsStore`. Each store mixes state + actions.
- **`src/hooks/`** — `useChat`, `useDocuments`, `useNotes`, `useSearch`, `useSettings`, `useKeyboard` (global shortcut handler).
- **`src/components/`** — organized by domain: `chat/`, `documents/`, `notes/`, `layout/` (sidebar + views), `settings/`, `search/`.
- **`src/types/index.ts`** — all TypeScript interfaces. Note: frontend types can diverge from backend Pydantic schemas in `api/schemas.py` — keep them in sync manually.
- **`vite.config.ts`** — `@` path alias → `src/`, dev proxy `/api` → `localhost:8765`.

### Key data flow

1. **Upload → Ingestion**: Frontend POSTs file to `/api/documents/upload` → service creates a DB row with `pending` status → background task calls `orchestrator.run_ingestion()` → LangGraph pipeline extracts/chunks/embeds/stores → status flips to `ready`.
2. **Chat**: Frontend POSTs to `/api/chat` → backend does hybrid search (vector + FTS5) → retrieves chunks → sends to chat provider → streams tokens back → verifier LLM checks citations.
3. **Settings**: Stored in both `app/config.py` (startup) and `settings` table (runtime). Frontend reads/writes via `/api/settings`. Provider selection and model names flow from here.

### Provider fallback chain

`ProviderRegistry.get_chat()` / `get_embedding()`: tries the user's preferred provider (ollama/openai); if it raises on init or returns None, falls back to local (embeddings) or mock. This means Ollama/OpenAI-compat providers are **lazy-initialized** — they only connect when first requested, and failures are logged as warnings, not crashes.

### Database conventions

- All tables use TEXT primary keys (UUIDs via `_new_id()` in `_shared.py`).
- `datetime('now')` used in DDL for timestamps.
- FTS5 virtual table `chunks_fts` mirrors chunk content; rebuilt after ingestion via `rebuild_fts()`.
- WAL journal mode, foreign keys ON, connection semaphore for concurrency control.

### Testing

- Backend: pytest + pytest-asyncio (auto mode). Tests in `hearth/tests/`. E2E journey tests in `test_journeys.py`.
- Frontend: no test runner configured yet — lint + typecheck only.
