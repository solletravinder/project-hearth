from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.storage.file_store import save_file
from app.storage.repository import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    update_document_status,
)

router = APIRouter(prefix="/api/documents")


def _infer_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mapping = {
        "pdf": "pdf",
        "epub": "epub",
        "md": "markdown",
        "mdown": "markdown",
        "markdown": "markdown",
        "txt": "text",
        "text": "text",
        "html": "html",
        "htm": "html",
        "mp3": "audio",
        "wav": "audio",
        "flac": "audio",
        "ogg": "audio",
        "m4a": "audio",
        "png": "image",
        "jpg": "image",
        "jpeg": "image",
        "gif": "image",
        "webp": "image",
        "svg": "image",
    }
    return mapping.get(ext, "other")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), folder: str = "default"):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    doc_type = _infer_type(file.filename)
    file_size = len(content)

    # Save file to disk using file_store
    file_path = await save_file(file.filename, content)

    doc = await create_document(
        title=file.filename,
        doc_type=doc_type,
        folder=folder,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
    )

    # Launch ingestion in background
    from app.pipeline.orchestrator import run_ingestion

    asyncio.create_task(
        run_ingestion(
            document_id=doc["id"],
            file_path=str(file_path),
            doc_type=doc_type,
            title=file.filename,
        )
    )

    return doc


@router.get("/")
async def list_docs(
    folder: Optional[str] = None,
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
):
    offset = (page - 1) * per_page
    docs = await list_documents(
        folder=folder,
        doc_type=doc_type,
        status=status,
        limit=per_page,
        offset=offset,
    )
    return {"items": docs, "page": page, "per_page": per_page}


@router.get("/{doc_id}")
async def get_doc(doc_id: str):
    doc = await get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{doc_id}/download")
async def download_document(doc_id: str):
    doc = await get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = Path(doc["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        path=str(file_path),
        media_type=doc.get("mime_type", "application/octet-stream"),
        filename=doc["title"],
    )


@router.post("/batch-delete", status_code=status.HTTP_200_OK)
async def batch_delete(request: BatchDeleteRequest):
    deleted = []
    for doc_id in request.ids:
        ok = await delete_document(doc_id)
        if ok:
            deleted.append(doc_id)
    return {"deleted": deleted}


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc(doc_id: str):
    deleted = await delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return None


@router.post("/{doc_id}/reindex")
async def reindex_document(doc_id: str):
    doc = await get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    updated = await update_document_status(doc_id, "pending")
    return updated


class BatchDeleteRequest(BaseModel):
    ids: list[str]
