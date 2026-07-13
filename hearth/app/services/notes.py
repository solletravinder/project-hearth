from app.storage.repos.notes import (
    create_note,
    delete_note,
    get_note,
    list_notes,
    update_note,
)


class NoteService:
    async def create_note(self, **kwargs) -> dict:
        return await create_note(**kwargs)

    async def get_note(self, note_id: str) -> dict | None:
        return await get_note(note_id)

    async def list_notes(self, **filters) -> list[dict]:
        return await list_notes(**filters)

    async def update_note(self, note_id: str, **fields) -> dict | None:
        return await update_note(note_id, **fields)

    async def delete_note(self, note_id: str) -> bool:
        return await delete_note(note_id)


note_service = NoteService()
