```markdown
---
name: hearth-e2e-test-strategy
---
Design Date: 2026-07-06
Type: specification

## Purpose
Define Hearth end-to-end test strategy focused on core user journey validation.

## Scope
Test the full system stack (FastAPI + SQLite + local models) through critical user workflows:
- Upload/ingest process
- Query pipeline with hybrid search
- Document lifecycle management

## Success Criteria
- <5s for small PDF ingestion (text extraction to query-ready)
- >80% relevant chunk retrieval on keyword queries
- Citations must reference actual document chunks from uploads
- Memory leak checks: DB connections closed after each operation

## Architecture
**Test Pyramid Position**
- E2E Layer: Full stack tests against live FastAPI server
- Integration Layer: API endpoint testing with controlled dependencies
- Unit Layer: Individual component testing (existing tests)

**Test Infrastructure**
- Pytest fixtures for temp DB, sample content, provider management
- @pytest.mark.e2e marker to distinguish from unit tests
- TestClient for API interaction
- Real SQLite with test-specific data per test
- Local model support for quality E2E validation

## Test Cases

### Ingest Journey Test Case
**Test**: test_ingest_and_query_flow
**Description**: Validate end-to-end document upload, processing and query pipeline
**Steps**:
1. Upload sample PDF via POST /api/documents/upload
2. Wait for ingestion completion via polling /api/documents/{id}/status
3. Submit query to POST /api/chat with hybrid search
4. Validate response contains expected content and citations

**Assertions**:
- Document appears in list via GET /api/documents
- Should provide answer referencing source chunks
- Cite verified via secondary LLM check

### Concurrent Query Test Case
**Test**: test_concurrent_queries
**Description**: Validate system performance under concurrent load
**Steps**:
1. Create baseline document using same ingest journey
2. Submit 3 queries simultaneously to POST /api/chat
3. Verify all complete with correct citations
4. Verify no partial results or timeouts

**Assertions**:
- All queries complete successfully
- Cited citations reference correct document chunks
- No correlation errors between concurrent threads

### Document Lifecycle Test Case
**Test**: test_document_lifecycle
**Description**: Validate document CRUD operations
**Steps**:
1. Create document via POST /api/documents/upload
2. Update content via PUT /api/documents/{id}/content
3. Verify preview accessible via GET /api/documents/{id}/preview
4. Delete document via DELETE /api/documents/{id}
5. Verify removal from /api/documents list

**Assertions**:
- All operations return appropriate HTTP status codes
- Content changes persist correctly
- Database state reflects all operations
- System auto-reindex on content change

### Notes CRUD Test Case
**Test**: test_notes_crud
**Description**: Validate notes management functionality
**Steps**:
1. Create note via POST /api/notes
2. Read note via GET /api/notes/{id}
3. Update note via PUT /api/notes/{id}
4. Delete note via DELETE /api/notes/{id}
5. Verify persistence changes in document store

**Assertions**:
- CRUD operations function correctly
- Data consistency maintained across storage
- Concurrent create/read scenarios supported

### Hybrid Search Ranking Test Case
**Test**: test_hybrid_search_ranking
**Description**: Validate BM25 + vector search integration
**Steps**:
1. Ingest documents with known keyword matches and semantic similarity
2. Submit query targeting multiple search dimensions
3. Verify result ranking includes both keyword and semantic matches
4. Confirm BM25 and vector scores are appropriately weighted

**Assertions**:
- Results ranked by combined relevance
- Integration of full-text + vector search functional
- Diversity of matches across search modes achieved

## Tooling & Runner Setup

### Test Infrastructure
- **conftest.py**: Fixtures for temp DB, sample content, and provider management
- **Marker**: @pytest.mark.e2e to distinguish from unit tests
- **API Testing**: TestClient for FastAPI interaction
- **Model Support**: Local Ollama/OpenAI-compat when available, MockProvider for CI fallbacks

### Test Organization
- **File**: backend/tests/test_journeys.py
- **Runner Commands**:
  - Full suite: pytest backend/tests/test_journeys.py -v --e2e --log-cli-level=INFO
  - Subset: pytest backend/tests/test_journeys.py -v -k "ingest or query"

### CI Integration
- Orchestration script: scripts/e2e_runner.py
- Smoke testing: python scripts/e2e_runner.py --smoke
- Model-specific reporting: python scripts/e2e_runner.py --report --model=<profile>

### Model Scope
- **Fast Profile**: Qwen3-0.6B for citation verification
- **Balanced Profile (Default)**: Qwen2.5-1.5B for generation
- Fallbacks enabled for CI environments without local models

## Resource Management
- **Database**: Temp SQLite with test data isolated per test
- **File System**: Temporary directories cleaned up after test completion
- **Memory**: Connection pooling with timeout < 1s per operation
- **Model Downloads**: Use existing Docker volumes to avoid re-downloading

## Cost Efficiency
- **Local Models**: Leverage Docker volumes for model persistence
- **Test Data Reuse**: Load test corpus once per test suite
- **Parallel Execution**: Configure pytest-xdist for concurrent test runs
- **CI Optimization**: Skip E2E when markers not provided

## Risks & Mitigations
- **Model Availability**: MockProvider coverage for offline CI runs
- **Resource Limits**: Container-level resource gating for CI
- **Test Stability**: Retries for transient database/network errors
- **PII Exposure**: Test data generated in isolated, non-production environments

## Implementation Dependencies
- Pytest + pytest-xdist (if parallel execution needed)
- FastAPI TestClient
- Model provider abstractions (backend/app/providers/registry.py)
- Test data generation utilities
- Clean-up utilities for temporary resources
```