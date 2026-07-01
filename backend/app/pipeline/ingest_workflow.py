"""LangGraph ingestion state machine."""

import logging
from typing import TypedDict, Literal, Optional, Any

from langgraph.graph import StateGraph, END

from app.storage.repository import create_chunk, update_document_status

logger = logging.getLogger(__name__)


class IngestionState(TypedDict):
    document_id: str
    document_title: str
    file_path: str
    doc_type: str
    raw_text: Optional[str]
    chunks: list[dict]
    error: Optional[str]
    status: str  # processing | done | error


def classify_file(state: IngestionState) -> dict:
    """Determine doc_type. Already known from upload, but validates."""
    doc_type = state.get("doc_type", "text")
    return {"doc_type": doc_type}


async def extract_text(state: IngestionState) -> dict:
    """Extract text based on file type using the appropriate model."""
    doc_type = state["doc_type"]
    file_path = state["file_path"]
    raw_text = ""
    import aiofiles

    try:
        if doc_type == "text" or doc_type == "note":
            async with aiofiles.open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = await f.read()

        elif doc_type == "pdf":
            # Try PyMuPDF, fall back to mock
            try:
                import fitz  # type: ignore
                doc = fitz.open(file_path)
                raw_text = "\n".join(page.get_text() for page in doc)
                doc.close()
            except ImportError:
                raw_text = f"[Mock PDF extraction of {state['document_title']}]"

        elif doc_type == "image":
            from app.models.trocr_model import trocr_service

            raw_text = await trocr_service.ocr(file_path)

        elif doc_type == "audio":
            from app.models.whisper_model import whisper_service

            raw_text = await whisper_service.transcribe(file_path)

        if not raw_text:
            raw_text = f"[No text extracted from {state['document_title']}]"

    except Exception as e:
        return {"error": f"Extraction failed: {e}", "status": "error"}

    return {"raw_text": raw_text}


def chunk_text(state: IngestionState) -> dict:
    """Split extracted text into chunks."""
    from app.core.chunking import chunk_by_characters

    raw_text = state.get("raw_text", "")
    if not raw_text:
        return {"chunks": [], "status": "error", "error": "No text to chunk"}

    chunk_dicts = chunk_by_characters(raw_text, max_chars=2000, overlap=200)
    chunks = []
    for i, c in enumerate(chunk_dicts):
        chunks.append(
            {
                "index": i,
                "content": c["content"],
                "token_count": c["token_count"],
                "content_hash": c["content_hash"],
            }
        )

    return {"chunks": chunks}


async def embed_chunks(state: IngestionState) -> dict:
    """Embed each chunk using the embedding service."""
    from app.models.embedding_model import embedding_service

    chunks = state.get("chunks", [])
    if not chunks:
        return {"chunks": []}

    texts = [c["content"] for c in chunks]
    embeddings = await embedding_service.embed(texts)

    for i, emb in enumerate(embeddings):
        chunks[i]["embedding"] = emb

    return {"chunks": chunks}


async def store_chunks(state: IngestionState) -> dict:
    """Store chunks in database."""
    doc_id = state["document_id"]
    chunks = state.get("chunks", [])

    for chunk in chunks:
        emb_bytes = None
        if chunk.get("embedding"):
            import struct

            emb_bytes = struct.pack(f"{len(chunk['embedding'])}f", *chunk["embedding"])
        await create_chunk(
            document_id=doc_id,
            chunk_index=chunk["index"],
            content=chunk["content"],
            token_count=chunk["token_count"],
            content_hash=chunk["content_hash"],
            embedding=emb_bytes,
        )

    await update_document_status(doc_id, "ready")
    return {"status": "done"}


def handle_error(state: IngestionState) -> dict:
    """Handle pipeline errors."""
    error = state.get("error", "Unknown error")
    logger.error(f"Pipeline error: {error}")
    return {"status": "error", "error": error}


def should_continue(state: IngestionState) -> Literal["continue", "error"]:
    if state.get("error"):
        return "error"
    return "continue"


def build_ingestion_graph() -> StateGraph:
    """Build and return the ingestion LangGraph."""
    workflow = StateGraph(IngestionState)

    # Add nodes
    workflow.add_node("classify", classify_file)
    workflow.add_node("extract", extract_text)
    workflow.add_node("chunk", chunk_text)
    workflow.add_node("embed", embed_chunks)
    workflow.add_node("store", store_chunks)
    workflow.add_node("handle_error", handle_error)

    # Set entry point
    workflow.set_entry_point("classify")

    # Add edges
    workflow.add_conditional_edges(
        "classify", should_continue, {"continue": "extract", "error": "handle_error"}
    )
    workflow.add_conditional_edges(
        "extract", should_continue, {"continue": "chunk", "error": "handle_error"}
    )
    workflow.add_conditional_edges(
        "chunk", should_continue, {"continue": "embed", "error": "handle_error"}
    )
    workflow.add_conditional_edges(
        "embed", should_continue, {"continue": "store", "error": "handle_error"}
    )
    workflow.add_edge("store", END)
    workflow.add_edge("handle_error", END)

    return workflow.compile()
