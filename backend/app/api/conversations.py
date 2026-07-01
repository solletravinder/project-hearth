from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status

from app.storage.repository import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
)

router = APIRouter(prefix="/api/conversations")


class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"
    model: str = "default"
    system_prompt: str = ""


@router.get("/")
async def list_convs(page: int = 1, per_page: int = 50):
    offset = (page - 1) * per_page
    convs = await list_conversations(limit=per_page, offset=offset)
    return {"items": convs, "page": page, "per_page": per_page}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_conv(body: CreateConversationRequest):
    conv = await create_conversation(
        title=body.title,
        model=body.model,
        system_prompt=body.system_prompt,
    )
    return conv


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conv(conv_id: str):
    deleted = await delete_conversation(conv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None


@router.get("/{conv_id}/messages")
async def get_conv_messages(conv_id: str, page: int = 1, per_page: int = 100):
    conv = await get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    offset = (page - 1) * per_page
    messages = await get_messages(conversation_id=conv_id, limit=per_page, offset=offset)
    return {"items": messages, "page": page, "per_page": per_page}
