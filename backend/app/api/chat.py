from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.storage.repository import (
    create_conversation,
    create_message,
    get_messages,
    get_conversation,
)

router = APIRouter(prefix="/api/chat")


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    context_docs: Optional[List[str]] = None


class RegenerateRequest(BaseModel):
    conversation_id: str
    message_id: Optional[str] = None


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

    mock_response = f"This is a mock assistant response to: '{body.query[:50]}...'"
    msg = await create_message(
        conversation_id=conv_id,
        role="assistant",
        content=mock_response,
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

    # Stub: regenerate the last assistant message
    mock_response = "This is a regenerated mock assistant response."
    msg = await create_message(
        conversation_id=body.conversation_id,
        role="assistant",
        content=mock_response,
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
