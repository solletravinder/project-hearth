
from app.storage.repos.conversations import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
)
from app.storage.repos.messages import create_message, get_messages


class ConversationService:
    async def create_conversation(self, title: str = "New Conversation", **kwargs) -> dict:
        return await create_conversation(title=title, **kwargs)

    async def get_conversation(self, conv_id: str) -> dict | None:
        return await get_conversation(conv_id)

    async def list_conversations(self, limit: int = 50, offset: int = 0) -> list[dict]:
        return await list_conversations(limit=limit, offset=offset)

    async def delete_conversation(self, conv_id: str) -> bool:
        return await delete_conversation(conv_id)

    async def create_message(
        self, conversation_id: str, role: str, content: str, **kwargs
    ) -> dict:
        return await create_message(
            conversation_id=conversation_id, role=role, content=content, **kwargs
        )

    async def get_messages(
        self, conversation_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        return await get_messages(conversation_id=conversation_id, limit=limit, offset=offset)


conversation_service = ConversationService()
