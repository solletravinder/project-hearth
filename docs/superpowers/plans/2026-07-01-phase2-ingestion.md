# Phase 2 — Ingestion Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Users can upload files (PDFs, images, audio, text), see them processed through an ingestion pipeline (classify → extract text → chunk → embed → store), and view results in the sidebar with real-time status updates.

**Architecture:** LangGraph state-machine pipeline orchestrates file processing. Model wrappers handle inference with graceful fallback (mock data if models not downloaded). Frontend polls document status or receives SSE updates.

**Tech Stack:** Python 3.12, LangGraph, faster-whisper, sentence-transformers, TrOCR, spaCy, sqlite-vec, aiofiles, React 18, Zustand, SSE

## Global Constraints

- No emojis in log messages, terminal output, or error messages — UI code can use emojis normally
- All processing is local — zero outbound calls
- Models are lazy-loaded on first use; pipeline works with mock data if models unavailable
- Ingestion runs asynchronously in the background (not blocking the upload response)
- Document status progresses: `pending` → `processing` → `ready` / `error`
- Chunks stored in both `chunks` table and `chunks_fts` (FTS5) for hybrid search
- Embeddings stored as binary blobs in `chunks.embedding` column
- The spec at `docs/superpowers/specs/2026-07-01-hearth-design.md` is the authoritative reference

---

## Task 1: Model Wrappers

**Branch:** `feat/backend-ingestion` (starts from master, sequential)

**Goal:** Real model wrapper classes with lazy loading and graceful fallback. Each wrapper implements a standard interface and can return mock data when the model isn't downloaded.

**Files:**
- Modify: `backend/app/models/manager.py` — proper singleton with TTL caching, async load, benchmark
- Create: `backend/app/models/whisper_model.py` — faster-whisper for speech-to-text
- Create: `backend/app/models/trocr_model.py` — TrOCR for image OCR
- Create: `backend/app/models/embedding_model.py` — sentence-transformers/gte-small for embeddings
- Create: `backend/app/models/ner_model.py` — spaCy for PII detection
- Modify: `backend/requirements.txt` — add model dependencies
- Create: `backend/tests/test_models.py` — model wrapper unit tests

---

- [ ] **Step 1.1: Update ModelManager**

Replace `backend/app/models/manager.py` with a complete async-ready manager:

- `ModelEntry` dataclass with name, status, loaded_at, memory_mb, error
- `ModelManager` singleton with:
  - `get_model(name)` → ModelEntry | None
  - `load_model(name, loader_callable)` → loads async, tracks TTL
  - `unload(name)` → bool
  - `get_status()` → dict of all models
  - `active_profile` tracking
- `model_manager` module-level instance

- [ ] **Step 1.2: Create Model Interfaces**

Define standard protocols:

```python
class EmbeddingModel(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

class TranscriptionModel(Protocol):
    async def transcribe(self, audio_path: str) -> str: ...

class OCRModel(Protocol):
    async def ocr(self, image_path: str) -> str: ...

class NERModel(Protocol):
    async def detect(self, text: str) -> list[dict]: ...
```

- [ ] **Step 1.3: Create embedding_model.py**

`EmbeddingService` class:
- Loads `gte-small` via `sentence-transformers` on first use
- `async embed(texts: list[str])` → list of 384-dim float lists
- Falls back to random 384-dim vectors if model not found
- Caches model in `model_manager`

- [ ] **Step 1.4: Create whisper_model.py**

`WhisperService` class:
- Loads `faster-whisper` base model on first use
- `async transcribe(audio_path)` → transcribed text string
- Falls back to mock transcription if model not found
- Supports .wav, .mp3, .m4a, .ogg files

- [ ] **Step 1.5: Create trocr_model.py**

`TROCRService` class:
- Loads TrOCR base-printed model via transformers on first use
- `async ocr(image_path)` → extracted text string
- Falls back to mock OCR if model not found
- Supports .png, .jpg, .jpeg, .webp

- [ ] **Step 1.6: Create ner_model.py**

`NERService` class:
- Loads `en_core_web_sm` spaCy model on first use
- `async detect(text)` → list of {type, start, end, text} dicts
- Falls back to regex-only detection if spaCy model not found

- [ ] **Step 1.7: Add dependencies to requirements.txt**

```text
# Model dependencies (optional — import errors handled gracefully)
sentence-transformers>=3.0.0
faster-whisper>=1.0.0
transformers>=4.40.0
spacy>=3.7.0
torch>=2.0.0
langgraph>=0.2.0
```

- [ ] **Step 1.8: Create model tests**

Test each wrapper's:
- Lazy loading (doesn't load on import)
- Fallback behavior (returns mock data when model absent)
- Error handling (graceful degradation)

---

## Task 2: Ingestion Pipeline

**Branch:** `feat/backend-ingestion` (continues from Task 1)

**Goal:** LangGraph state-machine pipeline that takes a file, classifies it, extracts text, chunks, embeds, and stores results.

**Files:**
- Create: `backend/app/pipeline/__init__.py`
- Create: `backend/app/pipeline/ingest_workflow.py`
- Create: `backend/app/pipeline/orchestrator.py`
- Create: `backend/tests/test_ingest.py`

---

- [ ] **Step 2.1: Define IngestionState and pipeline nodes**

`ingest_workflow.py`:

```python
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph

class IngestionState(TypedDict):
    document_id: str
    document_title: str
    file_path: str
    doc_type: Literal["pdf", "image", "audio", "text", "note"]
    raw_text: Optional[str]
    chunks: list[dict]
    error: Optional[str]
    status: str  # processing | done | error
```

Nodes (each is an async function):
1. `classify_file(state)` — determines doc_type from file extension and MIME
2. `extract_text(state)` — dispatches to correct extractor (TrOCR for images, faster-whisper for audio, PyMuPDF for PDF, direct read for text)
3. `chunk_text(state)` — splits text via `chunk_by_characters` or `chunk_by_tokens`
4. `embed_chunks(state)` — embeds each chunk via `embedding_model`
5. `store_chunks(state)` — inserts chunks into DB + FTS5 + vector index
6. `handle_error(state)` — sets status=error, logs trace

Edges: sequential with conditional error edges to `handle_error`.

- [ ] **Step 2.2: Create orchestrator**

`orchestrator.py`:

```python
from app.pipeline.ingest_workflow import build_ingestion_graph

ingestion_graph = build_ingestion_graph()

async def run_ingestion(document_id: str, file_path: str, doc_type: str, title: str) -> dict:
    """Run the ingestion pipeline for a document."""
    initial_state = IngestionState(
        document_id=document_id,
        file_path=file_path,
        doc_type=doc_type,
        document_title=title,
        raw_text=None,
        chunks=[],
        error=None,
        status="processing",
    )
    result = await ingestion_graph.ainvoke(initial_state)
    return result
```

- [ ] **Step 2.3: Create pipeline tests**

Test the full ingestion flow with mock models:
- Upload a text file → verify chunks created
- Upload an image → verify mock OCR runs
- Verify error handling for missing files

---

## Task 3: Wire Upload API to Pipeline + Search

**Branch:** `feat/backend-ingestion` (continues from Task 2)

**Goal:** Upload endpoint triggers ingestion pipeline as background task. Document list shows real status. Hybrid search endpoint works.

**Files:**
- Modify: `backend/app/api/documents.py` — trigger pipeline on upload
- Modify: `backend/app/api/documents.py` — add POST /batch-delete
- Modify: `backend/app/api/search.py` — implement hybrid search
- Modify: `backend/app/main.py` — register pipeline on startup if needed
- Create: `backend/tests/test_pipeline_integration.py`

---

- [ ] **Step 3.1: Update upload endpoint**

After creating the document, launch ingestion as a background task:

```python
@router.post("/upload", ...)
async def upload_document(file: UploadFile, folder: str = "default"):
    # ... create document ...
    # Launch ingestion in background
    asyncio.create_task(run_ingestion(
        document_id=doc["id"],
        file_path=str(file_path),
        doc_type=doc_type,
        title=file.filename,
    ))
    return doc
```

- [ ] **Step 3.2: Implement hybrid search**

Update `backend/app/api/search.py`:

```python
@router.get("/")
async def search(q: str, doc_type: str = None, page: int = 1, per_page: int = 10):
    # Hybrid: FTS5 BM25 + placeholder for vector similarity
    # Returns merged results with combined scores
```

Hybrid search formula: `score = 0.7 × cosine + 0.3 × BM25`

For Phase 2, since sqlite-vec may not be installed, implement FTS5 search with BM25 ranking as primary, and stub the vector portion.

- [ ] **Step 3.3: Add batch-delete endpoint**

```python
@router.post("/batch-delete")
async def batch_delete(doc_ids: list[str]):
    for doc_id in doc_ids:
        await delete_document(doc_id)
    return {"deleted": len(doc_ids)}
```

---

## Task 4: Frontend Document Management

**Branch:** `feat/frontend-docs` (parallel to backend)

**Goal:** Connects DocumentList, DocumentItem, and UploadZone to the real API. Shows live document processing status with progress indicators.

**Files:**
- Modify: `frontend/src/store/docStore.ts` — real API integration with polling
- Modify: `frontend/src/components/documents/DocumentList.tsx` — loading/empty/error states
- Modify: `frontend/src/components/documents/DocumentItem.tsx` — status badge animation
- Modify: `frontend/src/components/documents/UploadZone.tsx` — upload progress
- Create: `frontend/src/components/documents/ProcessingIndicator.tsx` — per-step status
- Modify: `frontend/src/api/client.ts` — ensure all endpoints matched

---

- [ ] **Step 4.1: Update API client**

Ensure `frontend/src/api/client.ts` has:
- `documents.upload(file, folder)` working
- `documents.list(params)` with status filter
- `documents.batchDelete(ids)`
- Polling helper for document status

- [ ] **Step 4.2: Update docStore with polling**

```typescript
// Add to docStore:
interface DocStore {
  // ...existing state...
  pollingInterval: number | null;
  startPolling: () => void;
  stopPolling: () => void;
}
```

When uploadFiles is called, start polling every 2 seconds until all uploading documents reach a terminal status (ready/error).

- [ ] **Step 4.3: Add ProcessingIndicator component**

Create a component that shows which step of ingestion a document is in:
- Queued → spinner icon
- Extracting → extraction icon
- Chunking → chunk icon
- Embedding → embed icon
- Storing → storage icon
- Complete → check icon

- [ ] **Step 4.4: Update UploadZone with progress**

- Show upload progress per file (bytes uploaded / total)
- After upload, show "Processing..." with ProcessingIndicator
- Disable upload while processing

- [ ] **Step 4.5: Update DocumentList with all states**

- Loading: show Spinner
- Empty: show EmptyState with upload CTA
- Error: show error message with retry
- Data: show DocumentItem list sorted by updated_at

- [ ] **Step 4.6: Update Sidebar to show document count**

Modify Sidebar to show the number of documents, notes, and conversations.

---

## Execution

Two parallel streams:

**Stream A (sequential, backend):** `feat/backend-ingestion`
- Task 1 → Task 2 → Task 3
- Each committed after tests pass

**Stream B (parallel, frontend):** `feat/frontend-docs`
- Task 4
- Committed after npm run build passes
