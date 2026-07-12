import pytest

from app.storage.database import check_db_health, init_db
from app.storage.repository import (
    create_conversation,
    create_document,
    create_message,
    create_note,
    get_document,
    get_messages,
    get_note,
    list_conversations,
    list_documents,
    list_notes,
)


@pytest.fixture(autouse=True)
async def setup_db():
    """Ensure DB is initialized before each test."""
    await init_db()
    yield


@pytest.mark.asyncio
async def test_create_and_get_document():
    """Test creating and retrieving a document."""
    doc = await create_document(
        title="Test Document",
        doc_type="text",
        file_path="/tmp/test.txt",
        file_size=1024,
        mime_type="text/plain",
    )

    assert doc is not None
    assert doc["title"] == "Test Document"
    assert doc["doc_type"] == "text"
    assert doc["status"] == "pending"

    retrieved = await get_document(doc["id"])
    assert retrieved is not None
    assert retrieved["id"] == doc["id"]
    assert retrieved["title"] == "Test Document"


@pytest.mark.asyncio
async def test_list_documents():
    """Test listing documents with filters."""
    await create_document(title="Doc A", doc_type="text")
    await create_document(title="Doc B", doc_type="markdown")
    await create_document(title="Doc C", doc_type="text", folder="research")

    all_docs = await list_documents()
    assert len(all_docs) >= 3

    text_docs = await list_documents(doc_type="text")
    assert all(d["doc_type"] == "text" for d in text_docs)

    folder_docs = await list_documents(folder="research")
    assert all(d["folder"] == "research" for d in folder_docs)


@pytest.mark.asyncio
async def test_create_conversation_and_messages():
    """Test creating a conversation and adding messages."""
    conv = await create_conversation(title="Test Conversation", model="default")

    assert conv is not None
    assert conv["title"] == "Test Conversation"

    msg1 = await create_message(
        conversation_id=conv["id"],
        role="user",
        content="Hello, how are you?",
    )
    assert msg1 is not None
    assert msg1["role"] == "user"

    msg2 = await create_message(
        conversation_id=conv["id"],
        role="assistant",
        content="I'm doing well, thank you!",
    )
    assert msg2 is not None
    assert msg2["role"] == "assistant"

    messages = await get_messages(conv["id"])
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_create_and_get_note():
    """Test creating and retrieving a note."""
    note = await create_note(
        title="Test Note", content="This is a test note.", tags=["test", "python"]
    )

    assert note is not None
    assert note["title"] == "Test Note"
    assert note["content"] == "This is a test note."

    retrieved = await get_note(note["id"])
    assert retrieved is not None
    assert retrieved["id"] == note["id"]


@pytest.mark.asyncio
async def test_list_notes():
    """Test listing notes."""
    await create_note(title="Note A", folder="personal")
    await create_note(title="Note B", folder="work")
    await create_note(title="Note C", folder="personal", pinned=True)

    notes = await list_notes()
    assert len(notes) >= 3

    personal = await list_notes(folder="personal")
    assert all(n["folder"] == "personal" for n in personal)


@pytest.mark.asyncio
async def test_list_conversations():
    """Test listing conversations."""
    await create_conversation(title="Chat 1")
    await create_conversation(title="Chat 2")

    convs = await list_conversations()
    assert len(convs) >= 2


@pytest.mark.asyncio
async def test_check_db_health():
    """Test database health check."""
    health = await check_db_health()
    assert health["status"] == "ok"
    assert "doc_count" in health
    assert "chunk_count" in health
