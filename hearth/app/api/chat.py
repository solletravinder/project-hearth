from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    BranchRequest,
    ChatRequest,
    ChatResponse,
    MessageResponse,
    RegenerateRequest,
)
from app.config import settings
from app.core.pii import redact_patterns
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


@router.post("/", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    conv_id = body.conversation_id

    if conv_id:
        conv = await get_conversation(conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = await create_conversation(title=body.query[:80])
        conv_id = conv["id"]

    query = body.query
    pii_redacted = False
    if await _is_pii_enabled():
        query, _ = redact_patterns(query)
        pii_redacted = query != body.query

    await create_message(
        conversation_id=conv_id,
        role="user",
        content=query,
        context_docs=body.context_docs,
    )

    provider = provider_registry.get_chat()
    if provider is not None:
        try:
            messages = [{"role": "user", "content": query}]
            profile = settings.profiles.get(settings.active_profile, {})
            temperature = profile.get("temperature", 0.7)
            response = await provider.chat(
                messages=messages,
                model=settings.default_model,
                temperature=temperature,
            )
        except Exception as e:
            logger.error("Chat provider failed: %s; falling back to mock", e)
            response = "[Assistant unavailable]"
    else:
        response = f"This is a mock assistant response to: '{body.query[:50]}...'"

    if pii_redacted:
        response, _ = redact_patterns(response)

    msg = await create_message(
        conversation_id=conv_id,
        role="assistant",
        content=response,
    )

    messages = await get_messages(conv_id)
    return ChatResponse(
        conversation_id=conv_id,
        message=MessageResponse(**msg),
        messages=[MessageResponse(**m) for m in messages],
        pii_redacted=pii_redacted,
    )


@router.post("/regenerate", response_model=ChatResponse)
async def regenerate(body: RegenerateRequest) -> ChatResponse:
    conv = await get_conversation(body.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    provider = provider_registry.get_chat()
    if provider is not None:
        try:
            last_messages = await get_messages(body.conversation_id, limit=10)
            provider_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in last_messages
                if m["role"] in ("user", "assistant", "system")
            ]
            response = await provider.chat(
                messages=provider_messages,
                model=settings.default_model,
            )
        except Exception as e:
            logger.error("Regeneration failed: %s; falling back to mock", e)
            response = "This is a regenerated mock assistant response."
    else:
        response = "This is a regenerated mock assistant response."

    pii_redacted = False
    if await _is_pii_enabled():
        redacted, _ = redact_patterns(response)
        pii_redacted = redacted != response
        response = redacted

    msg = await create_message(
        conversation_id=body.conversation_id,
        role="assistant",
        content=response,
    )
    return ChatResponse(
        conversation_id=body.conversation_id,
        message=MessageResponse(**msg),
        messages=[],
        pii_redacted=pii_redacted,
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
