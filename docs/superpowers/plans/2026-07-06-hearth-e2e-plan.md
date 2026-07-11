# Hearth E2E Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement end-to-end tests for Hearth's core user journeys: document ingestion, query pipeline, and document lifecycle.

**Architecture:** Pytest-based E2E tests against live FastAPI server with real SQLite. Tests use TestClient for API interaction, temp databases per test, and local model support with MockProvider fallbacks for CI.

**Tech Stack:** pytest, pytest-asyncio, FastAPI TestClient, httpx, SQLite (temp), local models (Qwen2.5-1.5B, Qwen3-0.6B)

## Global Constraints

- Tests placed in `backend/tests/` directory
- Use `@pytest.mark.e2e` marker to distinguish from unit tests
- Max 5s ingestion time for small PDFs
- >80% relevant chunk retrieval on keyword queries
- Citations must reference actual document chunks
- DB connections closed after each operation

---

## Test Infrastructure Setup

### Task 1: Configure E2E Marker in pytest

**Files:**
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Consumes: existing pytest configuration
- Produces: `pytest_configure()` hook with e2e marker

- [ ] **Step 1: Read current conftest.py**

```python
# Read backend/tests/conftest.py to see existing fixtures
```

- [ ] **Step 2: Add e2e marker configuration**

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
```

- [ ] **Step 3: Verify marker registration**

Run: `pytest backend/tests/ --collect-only -m e2e`
Expected: No errors about unknown marker

### Task 2: Create E2E Test File

**Files:**
- Create: `backend/tests/test_journeys.py`
- Create: `backend/tests/e2e/__init__.py` (empty)

**Interfaces:**
- Consumes: pytest markers, TestClient
- Produces: Test class with journey methods

- [ ] **Step 1: Create test file with imports**

```python
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)
```

- [ ] **Step 2: Create temp database fixture**

```python
@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    os.unlink(db_path)
```

- [ ] **Step 3: Verify file structure**

Run: `python -c "from tests.test_journeys import client; print('OK')"`
Expected: OK

### Task 3: Add Sample Test Content

**Files:**
- Create: `backend/tests/e2e/sample_content.py`
- Modify: `backend/tests/test_journeys.py`

**Interfaces:**
- Consumes: existing fixtures
- Produces: `sample_pdf()`, `sample_text()` fixtures

- [ ] **Step 1: Create sample content fixtures**

```python
# backend/tests/e2e/sample_content.py
SAMPLE_PDF = b"%PDF-1.4 sample content for testing"
SAMPLE_TEXT = "Hearth is an offline AI assistant for notes and research."
```

- [ ] **Step 2: Add fixtures to conftest.py**

```python
@pytest.fixture
def sample_pdf():
    return SAMPLE_PDF

@pytest.fixture
def sample_text():
    return SAMPLE_TEXT
```

- [ ] **Step 3: Run fixture test**

```python
def test_sample_content(sample_pdf, sample_text):
    assert sample_pdf is not None
    assert len(sample_text) > 0
```

---

## Test Case Implementation

### Task 4: Implement Ingest Journey Test

**Files:**
- Modify: `backend/tests/test_journeys.py`

**Interfaces:**
- Consumes: `client`, `temp_db`, `sample_pdf`
- Produces: `test_ingest_and_query_flow()`

- [ ] **Step 1: Write ingest and query test**

```python
@pytest.mark.e2e
def test_ingest_and_query_flow(client, temp_db, sample_pdf):
    # Upload document
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", sample_pdf, "application/pdf")}
    )
    assert response.status_code == 200
    doc_id = response.json()["id"]
    
    # Wait for ingestion (poll status)
    status_response = client.get(f"/api/documents/{doc_id}/status")
    assert status_response.status_code == 200
    
    # Query
    query_response = client.post(
        "/api/chat",
        json={"query": "What is Hearth?", "document_ids": [doc_id]}
    )
    assert query_response.status_code == 200
    assert "Hearth" in query_response.json()["answer"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_journeys.py::test_ingest_and_query_flow -v --tb=short`
Expected: FAIL (endpoints may not exist yet)

- [ ] **Step 3: Implement minimal API endpoints** (if needed)

Check if `/api/documents/upload`, `/api/documents/{id}/status`, `/api/chat` exist in backend/app/api/

### Task 5: Implement Concurrent Query Test

**Files:**
- Modify: `backend/tests/test_journeys.py`

**Interfaces:**
- Consumes: `client`, `temp_db`, `sample_pdf`
- Produces: `test_concurrent_queries()`

- [ ] **Step 1: Write concurrent query test**

```python
@pytest.mark.e2e
def test_concurrent_queries(client, temp_db, sample_pdf):
    import asyncio
    
    # Setup: ingest document first
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", sample_pdf, "application/pdf")}
    )
    doc_id = response.json()["id"]
    
    # Submit 3 concurrent queries
    queries = [
        {"query": "What is Hearth?", "document_ids": [doc_id]},
        {"query": "How does it work?", "document_ids": [doc_id]},
        {"query": "Is it private?", "document_ids": [doc_id]}
    ]
    
    # Run concurrently using asyncio
    async def run_queries():
        tasks = [
            asyncio.to_thread(
                client.post, "/api/chat", json=q
            ) for q in queries
        ]
        return await asyncio.gather(*tasks)
    
    results = asyncio.run(run_queries())
    
    for result in results:
        assert result.status_code == 200
```

- [ ] **Step 2: Run test**

Run: `pytest backend/tests/test_journeys.py::test_concurrent_queries -v`

### Task 6: Implement Document Lifecycle Test

**Files:**
- Modify: `backend/tests/test_journeys.py`

**Interfaces:**
- Consumes: `client`, `temp_db`
- Produces: `test_document_lifecycle()`

- [ ] **Step 1: Write document lifecycle test**

```python
@pytest.mark.e2e
def test_document_lifecycle(client, temp_db):
    # Create
    response = client.post(
        "/api/documents/upload",
        files={"file": ("lifecycle.pdf", b"test content", "application/pdf")}
    )
    doc_id = response.json()["id"]
    
    # Read
    read_response = client.get(f"/api/documents/{doc_id}")
    assert read_response.status_code == 200
    
    # Update
    update_response = client.put(
        f"/api/documents/{doc_id}/content",
        content="updated content"
    )
    assert update_response.status_code == 200
    
    # Delete
    delete_response = client.delete(f"/api/documents/{doc_id}")
    assert delete_response.status_code == 200
    
    # Verify deletion
    list_response = client.get("/api/documents")
    assert doc_id not in [d["id"] for d in list_response.json()]
```

- [ ] **Step 2: Run test**

Run: `pytest backend/tests/test_journeys.py::test_document_lifecycle -v`

### Task 7: Implement Notes CRUD Test

**Files:**
- Modify: `backend/tests/test_journeys.py`

**Interfaces:**
- Consumes: `client`
- Produces: `test_notes_crud()`

- [ ] **Step 1: Write notes CRUD test**

```python
@pytest.mark.e2e
def test_notes_crud(client):
    # Create
    create_response = client.post(
        "/api/notes",
        json={"title": "Test Note", "content": "Test content"}
    )
    assert create_response.status_code == 200
    note_id = create_response.json()["id"]
    
    # Read
    read_response = client.get(f"/api/notes/{note_id}")
    assert read_response.status_code == 200
    assert read_response.json()["title"] == "Test Note"
    
    # Update
    update_response = client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated Note", "content": "Updated content"}
    )
    assert update_response.status_code == 200
    
    # Delete
    delete_response = client.delete(f"/api/notes/{note_id}")
    assert delete_response.status_code == 200
```

- [ ] **Step 2: Run test**

Run: `pytest backend/tests/test_journeys.py::test_notes_crud -v`

### Task 8: Implement Hybrid Search Ranking Test

**Files:**
- Modify: `backend/tests/test_journeys.py`

**Interfaces:**
- Consumes: `client`, `temp_db`
- Produces: `test_hybrid_search_ranking()`

- [ ] **Step 1: Write hybrid search test**

```python
@pytest.mark.e2e
def test_hybrid_search_ranking(client, temp_db):
    # Ingest documents with different keyword densities
    doc1_response = client.post(
        "/api/documents/upload",
        files={"file": ("keywords.pdf", b"search keyword search keyword search", "application/pdf")}
    )
    doc1_id = doc1_response.json()["id"]
    
    doc2_response = client.post(
        "/api/documents/upload",
        files={"file": ("semantic.pdf", b"Different words same meaning", "application/pdf")}
    )
    doc2_id = doc2_response.json()["id"]
    
    # Query for keywords
    search_response = client.get(
        "/api/search",
        params={"query": "search", "document_ids": f"[{doc1_id}, {doc2_id}]"}
    )
    
    results = search_response.json()
    # Keywords doc should rank higher for "search" query
    assert results[0]["document_id"] == doc1_id
```

- [ ] **Step 2: Run test**

Run: `pytest backend/tests/test_journeys.py::test_hybrid_search_ranking -v`

---

## Runner Script Implementation

### Task 9: Create E2E Runner Script

**Files:**
- Create: `backend/scripts/e2e_runner.py`
- Modify: `pyproject.toml` (add script entry)

**Interfaces:**
- Consumes: pytest CLI
- Produces: Exit code 0 on success, non-zero on failure

- [ ] **Step 1: Create runner script**

```python
#!/usr/bin/env python3
import subprocess
import sys
import time
import os

def main():
    # Start server
    server = subprocess.Popen(
        ["uvicorn", "app.main:app", "--port", "8765"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for health check
        time.sleep(2)
        
        # Run tests
        result = subprocess.run(
            ["pytest", "tests/test_journeys.py", "-v", "-m", "e2e"],
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        return result.returncode
    finally:
        server.terminate()

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Add pyproject.toml entry**

```toml
[tool.poetry.scripts]
e2e-test = "scripts.e2e_runner:main"
```

- [ ] **Step 3: Test runner**

Run: `python backend/scripts/e2e_runner.py`
Expected: All tests pass

---

## CI Integration

### Task 10: Add CI Job

**Files:**
- Modify: `.github/workflows/ci.yml` (create if needed)

**Interfaces:**
- Consumes: GitHub Actions environment
- Produces: E2E test results in CI

- [ ] **Step 1: Add e2e job to CI workflow**

```yaml
e2e-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    - name: Run E2E tests
      run: cd backend && python scripts/e2e_runner.py
```

- [ ] **Step 2: Verify workflow syntax**

Run: `yamllint .github/workflows/ci.yml` (if available)

---

## Validation & Success Criteria

### Task 11: Verify Success Criteria

**Files:**
- All existing tests in `backend/tests/test_journeys.py`

**Interfaces:**
- Consumes: pytest output
- Produces: Pass/fail report against success criteria

- [ ] **Step 1: Run full E2E suite**

Run: `pytest backend/tests/test_journeys.py -v -m e2e --tb=short`

- [ ] **Step 2: Verify metrics**

Check:
- Ingestion time < 5s for small PDFs
- Relevant chunk retrieval > 80%
- Citations reference actual chunks
- DB connections closed (check logs)

- [ ] **Step 3: Generate report**

Output: `tests/e2e-report.txt` with pass/fail summary

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-06-hearth-e2e-plan.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach would you prefer?**