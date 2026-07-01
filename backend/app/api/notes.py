from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.storage.repository import (
    create_note,
    delete_note,
    get_note,
    list_notes,
    update_note,
)

router = APIRouter(prefix="/api/notes")


class CreateNoteRequest(BaseModel):
    title: str
    content: str = ""
    folder: str = "default"
    tags: list[str] | None = None
    pinned: bool = False
    source_document_id: str | None = None


class UpdateNoteRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    folder: str | None = None
    tags: list[str] | None = None
    pinned: bool | None = None


@router.get("/")
async def list_notes_endpoint(
    folder: str | None = None,
    pinned: bool | None = None,
    page: int = 1,
    per_page: int = 50,
):
    offset = (page - 1) * per_page
    notes = await list_notes(folder=folder, pinned=pinned, limit=per_page, offset=offset)
    return {"items": notes, "page": page, "per_page": per_page}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_note_endpoint(body: CreateNoteRequest):
    note = await create_note(
        title=body.title,
        content=body.content,
        folder=body.folder,
        tags=body.tags,
        pinned=body.pinned,
        source_document_id=body.source_document_id,
    )
    return note


@router.get("/{note_id}")
async def get_note_endpoint(note_id: str):
    note = await get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}")
async def update_note_endpoint(note_id: str, body: UpdateNoteRequest):
    existing = await get_note(note_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Note not found")

    updated = await update_note(
        note_id=note_id,
        title=body.title,
        content=body.content,
        folder=body.folder,
        tags=body.tags,
        pinned=body.pinned,
    )
    return updated


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note_endpoint(note_id: str):
    deleted = await delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return None
