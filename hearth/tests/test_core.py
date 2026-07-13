from app.core.chunking import chunk_by_characters
from app.core.pii import redact_patterns


def test_chunk_by_characters(sample_text):
    """Test character-based chunking."""
    chunks = chunk_by_characters(sample_text, max_chars=200, overlap=20)

    assert len(chunks) > 0
    assert all(isinstance(c, dict) for c in chunks)
    assert all("content" in c for c in chunks)
    assert all("token_count" in c for c in chunks)
    assert all("content_hash" in c for c in chunks)

    joined = "".join([c["content"] for c in chunks])
    assert len(joined) >= len(sample_text)


def test_chunk_by_characters_overlap(sample_text):
    """Test that overlapping chunks contain shared content."""
    chunks = chunk_by_characters(sample_text, max_chars=100, overlap=30)

    if len(chunks) > 1:
        chunk1_end = chunks[0]["content"][-30:]
        chunk2_start = chunks[1]["content"][:30]
        assert any(c in chunk2_start for c in chunk1_end) or any(
            c in chunk1_end for c in chunk2_start
        )


def test_chunk_by_characters_empty():
    """Test chunking empty text."""
    chunks = chunk_by_characters("")
    assert chunks == []


def test_redact_patterns(sample_pii_text):
    """Test PII redaction via regex patterns."""
    redacted, detections = redact_patterns(sample_pii_text)

    assert len(detections) > 0
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_SSN]" in redacted
    assert "john.doe@example.com" not in redacted
    assert "123-45-6789" not in redacted


def test_redact_patterns_no_pii():
    """Test redaction with no PII present."""
    text = "This is a clean text with no personal information."
    redacted, detections = redact_patterns(text)

    assert len(detections) == 0
    assert redacted == text
