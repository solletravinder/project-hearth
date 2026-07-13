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
python -m uvicorn app.main:app --reload --port 8765 # backend only
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

Hearth is a fully-offline, on-device AI notes & research assistant. Backend (FastAPI + SQLite) serves a React SPA and ML pipelines; frontend is a React Router SPA.

### Backend layers

- **`app/api/`** — REST routers, one per domain (chat, documents, notes, conversations, search, settings, models, system).
- **`app/services/`** — thin service layer. Handles business logic (e.g. triggering ingestion, PII redaction).
- **`app/storage/`** — data access. `schema.py` holds DDL. `database.py` manages sqlite connections. `repos/` holds entity-specific CRUD operations.
- **`app/pipeline/`** — LangGraph state machine for document ingestion. `orchestrator.py` triggers `ingest_workflow.py` graph nodes (classify → extract → chunk → embed → store).
- **`app/providers/`** — provider registry (`registry.py`) falling back from Ollama/OpenAI-compat to local/mock services.
- **`app/models/`** — local ML wrappers (Whisper for audio, TrOCR for OCR, spaCy/regex for PII, Sentence-Transformers for embeddings, and Llama.cpp for LLMs). Whisper transcription runs safely inside threadpools via `run_in_executor`.
- **`app/config.py`** — Pydantic configurations.

### Frontend structure (in `static/frontend/`)

- **`src/api/client.ts`** — API fetch client. Exposes modules for documents, conversations, chat, notes, settings, models, and search.
- **`src/store/`** — Zustand stores (`chatStore`, `docStore`, `settingsStore`).
- **`src/components/`** — domain specific components: `chat/`, `documents/`, `notes/`, `layout/`, `search/`, and `settings/` (contains `ModelManager` for SSE downloads, `ModelProfileCard` for profile changes, and `TraceInspector` for paginated logs).

### Key data flow & features

1. **Ingestion & Reindexing**: File upload saves to disk and spawns background LangGraph ingestion. Reindexing triggers the same `run_ingestion` workflow after status reset.
2. **Chat & PII Redaction**: User input is sent through sequential PII redaction: first fast regex patterns (email, phone, SSN), then spaCy NER (PERSON, ORG, GPE). Assistant responses undergo matching PII redaction before final display.
3. **Model Management**: SSE endpoint `/api/models/download/{name}/progress` streams download progress chunks back to the client while background download tasks download GGUFs from HuggingFace to the models directory.
4. **Log Inspection**: Raw entries from the `trace_log` table are served via `/api/system/logs` and rendered in the settings panel with visual status indicators.
5. **File Downloading**: Served directly via `GET /api/documents/{doc_id}/download` returning a `FileResponse` with MIME types.

### Testing

- Backend: pytest + pytest-asyncio (auto mode). E2E journey tests live in `test_journeys.py`.
- Frontend: lint + typecheck.
