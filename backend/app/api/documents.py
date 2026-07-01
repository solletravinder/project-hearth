from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status

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

    doc = await create_document(
        title=file.filename,
        doc_type=doc_type,
        folder=folder,
        file_path=f"uploads/{file.filename}",
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
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
