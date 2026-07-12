
import asyncio
import json
import logging
import re
import time
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    BranchRequest,
    ChatRequest,
    MessageResponse,
    RegenerateRequest,
)
from app.config import settings
from app.core.pii import redact_patterns
from app.models.ner_model import ner_service
from app.providers.registry import provider_registry
from app.storage.repos.conversations import (
    create_conversation,
    get_conversation,
)
from app.storage.repos.messages import create_message, get_messages
from app.storage.repos.settings import get_settings as get_settings_from_db

router = APIRouter(prefix="/api/chat")
logger = logging.getLogger(__name__)


async def _is_pii_enabled() -> bool:
    """Check whether PII filtering is turned on in settings."""
    db_settings = await get_settings_from_db()
    return db_settings.get("pii_filter_enabled", "false").lower() == "true"


async def _redact_pii(text: str) -> tuple[str, bool]:
    """Redact PII using regex patterns first, then NER for named entities.

    Running regex first means NER operates on already-cleaned text, so
    [REDACTED_...] placeholders are never double-processed.

    Returns (redacted_text, was_changed).
    """
    # 1. Fast regex pass (email, phone, SSN)
    redacted, _ = redact_patterns(text)

    # 2. NER pass for named entities (PERSON, ORG, GPE, etc.)
    try:
        ner_hits = await ner_service.detect(redacted)
        for hit in ner_hits:
            hit_text = hit.get("text", "")
            hit_type = hit.get("type", "ENTITY")
            # Skip anything that is already a redaction placeholder
            if hit_text and "[REDACTED_" not in hit_text:
                redacted = redacted.replace(hit_text, f"[REDACTED_{hit_type}]")
    except Exception as exc:
        logger.warning("NER PII detection failed: %s; falling back to regex-only", exc)

    return redacted, redacted != text


async def verify_citation(claim_context: str, chunk_content: str) -> bool:
    """Verify if a citation is supported by the chunk content using the chat LLM."""
    provider = provider_registry.get_chat()
    if provider is None:
        return True

    prompt = (
        "Task: Determine if the provided Text supports the claim.\n"
        f"Text: \"{chunk_content}\"\n"
        f"Claim: \"{claim_context[:200]}...\"\n\n"
        "Respond with only one word: SUPPORTED, UNSUPPORTED, or NOT_IN_CHUNK."
    )
    try:
        # Fast non-streaming call to check
        res = await provider.chat(
            messages=[{"role": "user", "content": prompt}],
            model=settings.default_model,
            temperature=0.0,
            max_tokens=10
        )
        return "SUPPORTED" in res.upper()
    except Exception as e:
        logger.warning("Citation verification failed: %s; default to True", e)
        return True


async def generate_chat_stream(body: ChatRequest, is_regen: bool = False) -> AsyncIterator[str]:
    """SSE generator yielding status, token, and done events."""
    conv_id = body.conversation_id

    if conv_id:
        conv = await get_conversation(conv_id)
        if not conv:
            yield f"event: error\ndata: {json.dumps({'message': 'Conversation not found', 'code': 'NOT_FOUND'})}\n\n"
            return
    else:
        if is_regen:
            yield f"event: error\ndata: {json.dumps({'message': 'Conversation ID required for regeneration', 'code': 'BAD_REQUEST'})}\n\n"
            return
        conv = await create_conversation(title=body.query[:80])
        conv_id = conv["id"]

    query = ""
    if is_regen:
        # Get last user message from conversation history
        history = await get_messages(conv_id, limit=20)
        user_msgs = [m for m in history if m["role"] == "user"]
        if not user_msgs:
            yield f"event: error\ndata: {json.dumps({'message': 'No user messages to regenerate', 'code': 'BAD_REQUEST'})}\n\n"
            return
        query = user_msgs[-1]["content"]
    else:
        query = body.query

    # 1. Redact PII in User Query (regex + NER)
    pii_redacted = False
    if await _is_pii_enabled():
        query, pii_redacted = await _redact_pii(query)

    # Save user message to database
    if not is_regen:
        await create_message(
            conversation_id=conv_id,
            role="user",
            content=query,
            context_docs=body.context_docs,
        )

    # 2. Hybrid Search for Context Chunks
    yield f"event: status\ndata: {json.dumps({'status': 'searching', 'documents': 0})}\n\n"
    await asyncio.sleep(0.1)

    from app.api.search import perform_hybrid_search
    chunks = await perform_hybrid_search(
        q=query,
        document_ids=body.context_docs,
        limit=5
    )

    yield f"event: status\ndata: {json.dumps({'status': 'searching', 'documents': len(chunks)})}\n\n"
    await asyncio.sleep(0.2)

    # 3. Build Prompt Context
    context_str = ""
    if chunks:
        context_str = "\n\n".join([
            f"Source {i+1} [{c['doc_title']} - chunk {c['chunk_id']}]:\n{c['content']}"
            for i, c in enumerate(chunks)
        ])

    db_settings = await get_settings_from_db()
    base_system_prompt = db_settings.get("system_prompt", "") or (
        "You are Hearth, a private, offline AI notes & research assistant. "
        "Answer the user's question based strictly on the provided context."
    )
    system_msg = f"{base_system_prompt}\n\nContext:\n{context_str}" if context_str else base_system_prompt

    # Gather recent conversation history
    history = await get_messages(conv_id, limit=10)
    provider_messages = [{"role": "system", "content": system_msg}]
    
    # Exclude system prompt and the last assistant message if regenerating
    msgs_to_append = history[:-1] if is_regen else history
    for m in msgs_to_append:
        if m["role"] in ("user", "assistant"):
            provider_messages.append({"role": m["role"], "content": m["content"]})

    yield f"event: status\ndata: {json.dumps({'status': 'generating'})}\n\n"

    # 4. Generate Chat Stream
    provider = provider_registry.get_chat()
    response_text = ""
    start_time = time.time()
    token_count = 0

    if provider is not None:
        try:
            async for token in provider.chat_stream(
                messages=provider_messages,
                model=settings.default_model,
                temperature=float(db_settings.get("temperature", 0.7)),
                max_tokens=int(db_settings.get("max_tokens", 2048)),
            ):
                response_text += token
                token_count += 1
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            logger.error("Chat streaming failed: %s", e)
            err_msg = f"\n[Chat provider failed: {e}]"
            response_text += err_msg
            yield f"event: token\ndata: {json.dumps({'token': err_msg})}\n\n"
    else:
        # Mock fallback streaming
        mock_text = f"This is a local mock assistant response to your query: '{query[:40]}...'"
        for word in mock_text.split(" "):
            token = word + " "
            response_text += token
            token_count += 1
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
            await asyncio.sleep(0.05)

    # 5. Redact PII in Assistant Output (regex + NER)
    if pii_redacted:
        response_text, _ = await _redact_pii(response_text)

    # 6. Parse and Verify Citations
    citations = []
    matches = re.findall(r"(?:\[Source\s+(\d+)\]|Source\s+(\d+))", response_text, re.IGNORECASE)
    found_indices = set()
    for m in matches:
        idx_str = m[0] or m[1]
        if idx_str:
            try:
                idx = int(idx_str) - 1
                if 0 <= idx < len(chunks):
                    found_indices.add(idx)
            except ValueError:
                continue

    for idx in sorted(found_indices):
        chunk = chunks[idx]
        verified = await verify_citation(response_text, chunk["content"])
        citations.append({
            "id": chunk["chunk_id"],
            "doc_title": chunk["doc_title"],
            "text": chunk["content"],
            "score": chunk["score"],
            "verified": verified,
            "color": "green" if verified else "amber"
        })

    # Save assistant message to database
    generation_ms = int((time.time() - start_time) * 1000)
    msg = await create_message(
        conversation_id=conv_id,
        role="assistant",
        content=response_text,
        citations=citations,
        token_count=token_count,
        generation_ms=generation_ms,
    )

    # 7. Complete SSE stream
    done_payload = {
        "citations": citations,
        "token_count": token_count,
        "generation_ms": generation_ms,
        "conversation_id": conv_id,
        "message": MessageResponse(
            id=msg["id"],
            conversation_id=msg["conversation_id"],
            role=msg["role"],
            content=msg["content"],
            context_docs=msg.get("context_docs"),
            tokens_in=msg.get("tokens_in", 0),
            tokens_out=msg.get("tokens_out", 0),
            created_at=msg["created_at"]
        ).model_dump()
    }
    yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"


@router.post("/")
async def chat(body: ChatRequest) -> StreamingResponse:
    """Stream chat responses via Server-Sent Events (SSE)."""
    return StreamingResponse(
        generate_chat_stream(body),
        media_type="text/event-stream"
    )


@router.post("/regenerate")
async def regenerate(body: RegenerateRequest) -> StreamingResponse:
    """Regenerate the last message using Server-Sent Events (SSE)."""
    # Wrap in ChatRequest for helper
    chat_req = ChatRequest(
        query="",
        conversation_id=body.conversation_id,
        context_docs=None
    )
    return StreamingResponse(
        generate_chat_stream(chat_req, is_regen=True),
        media_type="text/event-stream"
    )


@router.post("/branch")
async def branch(body: BranchRequest):
    conv = await get_conversation(body.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    branch_conv = await create_conversation(
        title=f"{conv['title']} (branch)",
        model=conv["model"],
        system_prompt=conv["system_prompt"],
        branch_from=body.conversation_id,
    )
    return {"conversation": branch_conv}
