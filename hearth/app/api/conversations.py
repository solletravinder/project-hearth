
from fastapi import APIRouter, HTTPException, status

from app.api.schemas import (
    ConversationListResponse,
    ConversationResponse,
    CreateConversationResponse,
    MessageListResponse,
    MessageResponse,
)
from app.storage.repos.conversations import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
)
from app.storage.repos.messages import get_messages

router = APIRouter(prefix="/api/conversations")


@router.get("/", response_model=ConversationListResponse)
async def list_convs(page: int = 1, per_page: int = 50) -> ConversationListResponse:
    offset = (page - 1) * per_page
    convs = await list_conversations(limit=per_page, offset=offset)
    return ConversationListResponse(
        items=[ConversationResponse(**c) for c in convs], page=page, per_page=per_page
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CreateConversationResponse)
async def create_conv(body: dict) -> CreateConversationResponse:
    conv = await create_conversation(
        title=body.get("title", "New Conversation"),
        model=body.get("model", "default"),
        system_prompt=body.get("system_prompt", ""),
    )
    return CreateConversationResponse(**conv)


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conv(conv_id: str):
    deleted = await delete_conversation(conv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None


@router.get("/{conv_id}/messages", response_model=MessageListResponse)
async def get_conv_messages(
    conv_id: str, page: int = 1, per_page: int = 100
) -> MessageListResponse:
    conv = await get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    offset = (page - 1) * per_page
    messages = await get_messages(conversation_id=conv_id, limit=per_page, offset=offset)
    return MessageListResponse(
        items=[MessageResponse(**m) for m in messages], page=page, per_page=per_page
    )
