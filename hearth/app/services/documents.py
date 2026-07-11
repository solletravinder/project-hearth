from __future__ import annotations

from app.storage.repos.documents import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    update_document_status,
)
from app.storage.repos.chunks import create_chunk, rebuild_fts


class DocumentService:
    async def create_document(self, **kwargs) -> dict:
        return await create_document(**kwargs)

    async def get_document(self, doc_id: str) -> dict | None:
        return await get_document(doc_id)

    async def list_documents(self, **filters) -> list[dict]:
        return await list_documents(**filters)

    async def update_status(self, doc_id: str, status: str, metadata: dict | None = None) -> dict | None:
        return await update_document_status(doc_id, status, metadata)

    async def delete_document(self, doc_id: str) -> bool:
        return await delete_document(doc_id)

    async def store_chunks(self, document_id: str, chunks: list[dict]) -> None:
        for chunk in chunks:
            emb_bytes = None
            if chunk.get("embedding"):
                import struct
                emb_bytes = struct.pack(f"{len(chunk['embedding'])}f", *chunk["embedding"])
            await create_chunk(
                document_id=document_id,
                chunk_index=chunk["index"],
                content=chunk["content"],
                token_count=chunk["token_count"],
                content_hash=chunk["content_hash"],
                embedding=emb_bytes,
            )
        await rebuild_fts()


document_service = DocumentService()
