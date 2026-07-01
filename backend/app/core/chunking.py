from __future__ import annotations

import hashlib
from typing import List


def chunk_by_characters(
    text: str, max_chars: int = 2000, overlap: int = 200
) -> List[dict]:
    """Split text into overlapping chunks by character count."""
    if not text:
        return []

    chunks: List[dict] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + max_chars, text_len)
        chunk_text = text[start:end]
        content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

        chunks.append(
            {
                "content": chunk_text,
                "token_count": len(chunk_text) // 4,  # rough estimate
                "content_hash": content_hash,
            }
        )

        if end >= text_len:
            break

        start += max_chars - overlap

    return chunks


def chunk_by_tokens(
    text: str,
    tokenizer,
    max_tokens: int = 512,
    overlap: int = 64,
) -> List[dict]:
    """Split text into overlapping chunks by token count using a tokenizer."""
    if not text:
        return []

    tokens = tokenizer.encode(text)
    chunks: List[dict] = []
    start = 0
    token_len = len(tokens)

    while start < token_len:
        end = min(start + max_tokens, token_len)
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

        chunks.append(
            {
                "content": chunk_text,
                "token_count": len(chunk_tokens),
                "content_hash": content_hash,
            }
        )

        if end >= token_len:
            break

        start += max_tokens - overlap

    return chunks
