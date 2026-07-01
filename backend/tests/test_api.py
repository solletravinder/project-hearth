from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import create_app


def test_health():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/system/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "0.1.0"
        assert data["status"] == "ok"
        assert "database" in data
        assert "models" in data


def test_list_documents_empty():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/documents/")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["page"] == 1


def test_list_notes_empty():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/notes/")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["page"] == 1


def test_list_conversations_empty():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/conversations/")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["page"] == 1


def test_chat_stub():
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/api/chat/", json={"query": "Hello, world!"})
        assert resp.status_code == 200
        data = resp.json()
        assert "conversation_id" in data
        assert "message" in data
        assert data["message"]["role"] == "assistant"


def test_model_status():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/models/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "loaded_count" in data


def test_document_upload():
    app = create_app()
    with TestClient(app) as client:
        file_content = io.BytesIO(b"This is a test document content.")
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", file_content, "text/plain")},
            params={"folder": "test"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "test.txt"
        assert data["doc_type"] == "text"
        assert data["folder"] == "test"


def test_get_nonexistent_document():
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/documents/nonexistent-id")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Document not found"
