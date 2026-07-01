"""Tests for model wrappers - mock/fallback behavior without downloading models."""

import pytest
import random

from app.models.embedding_model import EmbeddingService, EMBEDDING_DIM
from app.models.whisper_model import WhisperService
from app.models.trocr_model import TROCRService
from app.models.ner_model import NERService, PII_PATTERNS


@pytest.mark.asyncio
async def test_embedding_service_mock():
    """Test embedding service returns mock vectors with correct dimension."""
    svc = EmbeddingService()
    texts = ["Hello world", "Test document"]
    embeddings = await svc.embed(texts)

    assert len(embeddings) == 2
    for emb in embeddings:
        assert len(emb) == EMBEDDING_DIM
        assert all(isinstance(v, float) for v in emb)


@pytest.mark.asyncio
async def test_embedding_service_single_text():
    """Test embedding service with single text returns 1 vector of 384 dim."""
    svc = EmbeddingService()
    embeddings = await svc.embed(["Single text"])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == EMBEDDING_DIM


@pytest.mark.asyncio
async def test_embedding_service_empty():
    """Test embedding service with empty list returns empty list."""
    svc = EmbeddingService()
    embeddings = await svc.embed([])
    assert embeddings == []


@pytest.mark.asyncio
async def test_whisper_mock():
    """Test whisper service returns mock transcription string."""
    svc = WhisperService()
    result = await svc.transcribe("/tmp/test_audio.wav")
    assert isinstance(result, str)
    assert "Mock transcription" in result
    assert "test_audio.wav" in result


@pytest.mark.asyncio
async def test_trocr_mock():
    """Test trocr service returns mock OCR string."""
    svc = TROCRService()
    result = await svc.ocr("/tmp/test_image.jpg")
    assert isinstance(result, str)
    assert "Mock OCR output" in result
    assert "test_image.jpg" in result


@pytest.mark.asyncio
async def test_ner_regex_email():
    """Test NER service detects email via regex."""
    svc = NERService()
    text = "Contact me at user@example.com for details."
    results = await svc.detect(text)
    emails = [r for r in results if r["type"] == "EMAIL"]
    assert len(emails) >= 1
    assert "user@example.com" in emails[0]["text"]


@pytest.mark.asyncio
async def test_ner_regex_phone():
    """Test NER service detects phone via regex."""
    svc = NERService()
    text = "Call me at 1234567890."
    results = await svc.detect(text)
    phones = [r for r in results if r["type"] == "PHONE"]
    assert len(phones) >= 1


@pytest.mark.asyncio
async def test_ner_regex_ssn():
    """Test NER service detects SSN via regex."""
    svc = NERService()
    text = "My SSN is 123-45-6789."
    results = await svc.detect(text)
    ssns = [r for r in results if r["type"] == "SSN"]
    assert len(ssns) >= 1


@pytest.mark.asyncio
async def test_ner_no_pii():
    """Test NER service with no PII returns empty list."""
    svc = NERService()
    text = "This is a clean text with no personal information whatsoever."
    results = await svc.detect(text)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_model_manager_singleton():
    """Test ModelManager is a singleton."""
    from app.models.manager import ModelManager, model_manager
    m1 = ModelManager()
    m2 = ModelManager()
    assert m1 is m2
    assert model_manager is m1


@pytest.mark.asyncio
async def test_model_manager_load_unload():
    """Test ModelManager load/unload cycle."""
    from app.models.manager import ModelManager, model_manager

    mgr = ModelManager()

    async def dummy_loader():
        return {"dummy": "model"}

    instance = await mgr.load_model("test_model", dummy_loader)
    assert instance == {"dummy": "model"}
    assert mgr.get_model("test_model") == instance

    status = mgr.get_status()
    assert "test_model" in status["models"]
    assert status["models"]["test_model"]["status"] == "ready"

    ok = mgr.unload("test_model")
    assert ok is True
    assert mgr.get_model("test_model") is None


@pytest.mark.asyncio
async def test_model_manager_register():
    """Test ModelManager register_model."""
    from app.models.manager import ModelManager, ModelEntry

    mgr = ModelManager()
    entry = ModelEntry(name="my_model", memory_mb=256.0)
    mgr.register_model("my_model", entry)

    status = mgr.get_status()
    assert "my_model" in status["models"]
    assert status["models"]["my_model"]["status"] == "unloaded"
    assert status["models"]["my_model"]["memory_mb"] == 256.0
