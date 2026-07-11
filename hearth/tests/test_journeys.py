"""End-to-end journey tests for Hearth core functionality."""

from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.storage.database import init_db


@pytest.fixture
def client():
    """Create a TestClient for the Hearth application."""
    app = create_app()
    return TestClient(app)


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

    # Get document to check status
    status_response = client.get(f"/api/documents/{doc_id}")
    assert status_response.status_code == 200, f"Get document failed: {status_response.text}"

    # Query using context_docs (equivalent to document_ids in plan)
    query_response = client.post(
        "/api/chat/",
        json={"query": "What is Hearth?", "context_docs": [doc_id]}
    )
    assert query_response.status_code == 200, f"Query failed: {query_response.text}"
    result = query_response.json()
    assert "conversation_id" in result
    assert "message" in result
    assert result["message"]["role"] == "assistant"
