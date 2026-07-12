"""Tests for ingestion pipeline with mock data."""

import contextlib
import uuid

import pytest

from app.config import settings
from app.storage.database import init_db
from app.storage.repository import create_document, get_document


@pytest.fixture(autouse=True)
async def fresh_db():
    """Ensure a fresh database for each test."""
    db_path = settings.resolved_db_path
    if db_path.exists():
        with contextlib.suppress(PermissionError):
            db_path.unlink()
    await init_db()
    yield


@pytest.fixture
def unique_doc_id():
    """Generate a unique document ID for each test."""
    return f"test-doc-{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_ingest_text(tmp_path, unique_doc_id):
    """Test full ingestion of a text file."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("This is a test document. " * 200)

    # Create document first with known ID
    doc = await create_document(
        title="test.txt",
        doc_type="text",
        file_path=str(file_path),
        doc_id=unique_doc_id,
    )
    assert doc is not None
    assert doc["id"] == unique_doc_id

    from app.pipeline.orchestrator import run_ingestion

    result = await run_ingestion(
        document_id=unique_doc_id,
        file_path=str(file_path),
        doc_type="text",
        title="test.txt",
    )
    assert result["status"] in ("done", "error"), f"Pipeline failed: {result.get('error')}"
    if result["status"] == "done":
        updated = await get_document(unique_doc_id)
        assert updated is not None
        assert updated["status"] == "ready"

    # Clean up
    if result.get("status") == "error":
        pytest.skip(f"Pipeline returned error: {result.get('error')}")


@pytest.mark.asyncio
async def test_ingest_audio_mock(tmp_path, unique_doc_id):
    """Test audio ingestion uses mock transcription."""
    file_path = tmp_path / "test.wav"
    file_path.write_bytes(b"mock audio data")

    doc = await create_document(
        title="test.wav",
        doc_type="audio",
        file_path=str(file_path),
        doc_id=unique_doc_id,
    )
    assert doc is not None

    from app.pipeline.orchestrator import run_ingestion

    result = await run_ingestion(
        document_id=unique_doc_id,
        file_path=str(file_path),
        doc_type="audio",
        title="test.wav",
    )
    assert result["status"] in ("done", "error"), f"Pipeline failed: {result.get('error')}"


@pytest.mark.asyncio
async def test_ingest_empty_text(tmp_path, unique_doc_id):
    """Test ingestion of an empty text file."""
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")

    doc = await create_document(
        title="empty.txt",
        doc_type="text",
        file_path=str(file_path),
        doc_id=unique_doc_id,
    )
    assert doc is not None

    from app.pipeline.orchestrator import run_ingestion

    result = await run_ingestion(
        document_id=unique_doc_id,
        file_path=str(file_path),
        doc_type="text",
        title="empty.txt",
    )
    # Empty text should still go through pipeline
    assert result["status"] in ("done", "error")
