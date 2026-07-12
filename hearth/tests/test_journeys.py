"""End-to-end journey tests for Hearth core functionality."""

import concurrent.futures
import json
import os
import tempfile
import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.storage.database import init_db


@pytest.fixture
def client():
    """Create a TestClient for the Hearth application."""
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
async def setup_db():
    """Ensure DB is initialized before each test."""
    await init_db()
    yield


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


# Sample content for tests
SAMPLE_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
SAMPLE_TEXT = "Hearth is an offline AI assistant for notes and research."


@pytest.fixture
def sample_pdf():
    """Provide sample PDF content for testing."""
    return SAMPLE_PDF


@pytest.fixture
def sample_text():
    """Provide sample text content for testing."""
    return SAMPLE_TEXT


def test_sample_content(sample_pdf, sample_text):
    """Test that sample content fixtures are available."""
    assert sample_pdf is not None
    assert len(sample_text) > 0


def parse_sse_response(response):
    """Helper to parse event streams from a StreamingResponse."""
    event = None
    tokens = []
    done_data = None
    for line in response.iter_lines():
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        line = line.strip()
        if not line:
            continue
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: "):
            data_str = line[6:]
            data = json.loads(data_str)
            if event == "token":
                tokens.append(data["token"])
            elif event == "done":
                done_data = data
    return "".join(tokens), done_data


def wait_for_document_ready(client, doc_id, timeout=10):
    """Poll document status until it becomes ready or times out."""
    start = time.time()
    while time.time() - start < timeout:
        resp = client.get(f"/api/documents/{doc_id}")
        if resp.status_code == 200 and resp.json().get("status") == "ready":
            return True
        time.sleep(0.05)
    return False


@pytest.mark.e2e
def test_ingest_and_query_flow(client, sample_pdf):
    """Test document ingestion and query flow."""
    # Upload document
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", sample_pdf, "application/pdf")}
    )
    assert response.status_code == 201, f"Upload failed: {response.text}"
    doc_id = response.json()["id"]

    # Wait for ready status
    assert wait_for_document_ready(client, doc_id), "Document processing timed out"

    # Query using context_docs
    query_response = client.post(
        "/api/chat/",
        json={"query": "What is Hearth?", "context_docs": [doc_id]}
    )
    assert query_response.status_code == 200, f"Query failed: {query_response.text}"

    text, done = parse_sse_response(query_response)
    assert len(text) > 0
    assert done is not None
    assert "conversation_id" in done
    assert done["message"]["role"] == "assistant"


@pytest.mark.e2e
def test_concurrent_queries(client, sample_pdf):
    """Validate system performance and safety under concurrent queries."""
    # Upload document
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", sample_pdf, "application/pdf")}
    )
    doc_id = response.json()["id"]

    # Wait for ready status
    assert wait_for_document_ready(client, doc_id), "Document processing timed out"

    queries = [
        "What is Hearth?",
        "Is Hearth offline?",
        "Does Hearth run locally?"
    ]

    def send_query(q):
        resp = client.post(
            "/api/chat/",
            json={"query": q, "context_docs": [doc_id]}
        )
        return resp

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(send_query, queries))

    for resp in results:
        assert resp.status_code == 200
        text, done = parse_sse_response(resp)
        assert len(text) > 0
        assert done is not None


@pytest.mark.e2e
def test_document_lifecycle(client):
    """Validate document lifecycle CRUD operations."""
    # 1. Create (upload)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("lifecycle.txt", b"This is lifecycle test content", "text/plain")}
    )
    assert response.status_code == 201
    doc = response.json()
    doc_id = doc["id"]

    # Wait for ready status
    assert wait_for_document_ready(client, doc_id), "Document processing timed out"

    # Get document details
    status_resp = client.get(f"/api/documents/{doc_id}")
    assert status_resp.status_code == 200

    # 2. Delete document
    delete_resp = client.delete(f"/api/documents/{doc_id}")
    assert delete_resp.status_code == 204

    # Verify removal
    list_resp = client.get("/api/documents/")
    assert list_resp.status_code == 200
    doc_ids = [d["id"] for d in list_resp.json()["items"]]
    assert doc_id not in doc_ids


@pytest.mark.e2e
def test_notes_crud(client):
    """Validate notes management CRUD operations."""
    # 1. Create Note
    create_resp = client.post(
        "/api/notes/",
        json={"title": "E2E Note", "content": "Initial E2E test content"}
    )
    assert create_resp.status_code in (200, 201)
    note = create_resp.json()
    note_id = note["id"]

    # 2. Read Note
    get_resp = client.get(f"/api/notes/{note_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "E2E Note"

    # 3. Update Note
    update_resp = client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated E2E Note", "content": "Modified content"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated E2E Note"

    # 4. Delete Note
    delete_resp = client.delete(f"/api/notes/{note_id}")
    assert delete_resp.status_code == 204

    # Verify deletion
    verify_resp = client.get(f"/api/notes/{note_id}")
    assert verify_resp.status_code == 404


@pytest.mark.e2e
def test_hybrid_search_ranking(client):
    """Validate BM25 + vector hybrid ranking on keywords."""
    # Ingest document 1 with high keyword density
    resp1 = client.post(
        "/api/documents/upload",
        files={"file": ("kw1.txt", b"hearth hearth hearth assistant notes", "text/plain")}
    )
    doc1_id = resp1.json()["id"]

    # Ingest document 2 with semantic description
    resp2 = client.post(
        "/api/documents/upload",
        files={"file": ("sem2.txt", b"fully offline private software application", "text/plain")}
    )
    doc2_id = resp2.json()["id"]

    # Wait for both to be ready
    assert wait_for_document_ready(client, doc1_id), "Document 1 processing timed out"
    assert wait_for_document_ready(client, doc2_id), "Document 2 processing timed out"

    # Query for "hearth"
    search_resp = client.get("/api/search/", params={"q": "hearth"})
    assert search_resp.status_code == 200
    results = search_resp.json()["results"]

    # Doc 1 (highly relevant to "hearth") should rank first
    assert len(results) > 0
    assert results[0]["document_id"] == doc1_id
