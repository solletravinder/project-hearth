from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.providers.registry import provider_registry
from app.storage.repository import (
    create_conversation,
    create_message,
    get_conversation,
    get_messages,
)

router = APIRouter(prefix="/api/chat")

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    context_docs: list[str] | None = None


class RegenerateRequest(BaseModel):
    conversation_id: str
    message_id: str | None = None


class BranchRequest(BaseModel):
    conversation_id: str
    message_id: str


@router.post("/")
async def chat(body: ChatRequest):
    conv_id = body.conversation_id

    if conv_id:
        conv = await get_conversation(conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = await create_conversation(title=body.query[:80])
        conv_id = conv["id"]

    await create_message(
        conversation_id=conv_id,
        role="user",
        content=body.query,
        context_docs=body.context_docs,
    )

    # Try provider-based chat, fall back to mock
    provider = provider_registry.get_chat()
    if provider is not None:
        try:
            messages = [{"role": "user", "content": body.query}]
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

    msg = await create_message(
        conversation_id=conv_id,
        role="assistant",
        content=response,
    )

    messages = await get_messages(conv_id)
    return {
        "conversation_id": conv_id,
        "message": msg,
        "messages": messages,
    }


@router.post("/regenerate")
async def regenerate(body: RegenerateRequest):
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

    msg = await create_message(
        conversation_id=body.conversation_id,
        role="assistant",
        content=response,
    )
    return {"message": msg}


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
