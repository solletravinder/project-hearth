from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import (
    CreateNoteRequest,
    NoteListResponse,
    NoteResponse,
    UpdateNoteRequest,
)
from app.storage.repos.notes import (
    create_note,
    delete_note,
    get_note,
    list_notes,
    update_note,
)

router = APIRouter(prefix="/api/notes")


@router.get("/", response_model=NoteListResponse)
async def list_notes_endpoint(
    folder: str | None = None,
    pinned: bool | None = None,
    page: int = 1,
    per_page: int = 50,
) -> NoteListResponse:
    offset = (page - 1) * per_page
    notes = await list_notes(folder=folder, pinned=pinned, limit=per_page, offset=offset)
    return NoteListResponse(
        items=[NoteResponse(**n) for n in notes], page=page, per_page=per_page
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=NoteResponse)
async def create_note_endpoint(body: CreateNoteRequest) -> NoteResponse:
    note = await create_note(
        title=body.title,
        content=body.content,
        folder=body.folder,
        tags=body.tags,
        pinned=body.pinned,
        source_document_id=body.source_document_id,
    )
    return NoteResponse(**note)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note_endpoint(note_id: str) -> NoteResponse:
    note = await get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(**note)


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note_endpoint(note_id: str, body: UpdateNoteRequest) -> NoteResponse:
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
    return NoteResponse(**(updated or {}))


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note_endpoint(note_id: str):
    deleted = await delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return None
