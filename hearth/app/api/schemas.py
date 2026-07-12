"""Shared Pydantic schemas for API request/response validation."""


from pydantic import BaseModel

# ─── Documents ───────────────────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    id: str
    title: str
    doc_type: str
    status: str
    folder: str
    file_path: str | None = None
    file_size: int = 0
    mime_type: str | None = None
    metadata: dict[str, object] | None = None
    word_count: int = 0
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    page: int
    per_page: int


class BatchDeleteRequest(BaseModel):
    ids: list[str]


class BatchDeleteResponse(BaseModel):
    deleted: list[str]


# ─── Conversations ───────────────────────────────────────────────────────────


class ConversationResponse(BaseModel):
    id: str
    title: str
    model: str
    system_prompt: str
    message_count: int
    branch_from: str | None = None
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    page: int
    per_page: int


class CreateConversationResponse(BaseModel):
    id: str
    title: str
    model: str
    system_prompt: str
    message_count: int
    branch_from: str | None = None
    created_at: str
    updated_at: str


# ─── Messages ────────────────────────────────────────────────────────────────


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    context_docs: list[str] | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    created_at: str


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    page: int
    per_page: int


# ─── Notes ───────────────────────────────────────────────────────────────────


class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    folder: str
    tags: list[str] | None = None
    pinned: bool = False
    source_document_id: str | None = None
    created_at: str
    updated_at: str


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    page: int
    per_page: int


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


# ─── Chat ────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    context_docs: list[str] | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    messages: list[MessageResponse]
    pii_redacted: bool = False


class RegenerateRequest(BaseModel):
    conversation_id: str
    message_id: str | None = None


class BranchRequest(BaseModel):
    conversation_id: str
    message_id: str


# ─── Search ───────────────────────────────────────────────────────────────────


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    doc_title: str
    doc_type: str
    token_count: int
    score: float
    source_type: str = "document"


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    page: int
    per_page: int
    query: str


# ─── Settings ────────────────────────────────────────────────────────────────


class SettingsResponse(BaseModel):
    settings: dict[str, object]


# ─── System ──────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    version: str
    status: str
    database: dict[str, object]
    models: dict[str, object]
