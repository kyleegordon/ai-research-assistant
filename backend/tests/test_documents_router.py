"""Tests for routers/documents.py via FastAPI's TestClient.

This router is a thin wrapper around services.documents.list_documents() and
delete_document(). Both are monkeypatched here for the same reason as in
test_documents.py: real chromadb.PersistentClient(path="./chroma_db") must
never be touched by tests. The underlying functions' own behavior is already
covered directly in test_documents.py — these tests just confirm the HTTP
plumbing (status codes, response shape) is wired up correctly.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import routers.documents as documents_router_module
from routers.documents import router as documents_router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(documents_router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestGetDocuments:
    def test_returns_documents_list_from_service(self, client, monkeypatch):
        monkeypatch.setattr(
            documents_router_module,
            "list_documents",
            lambda: [{"filename": "report.pdf", "chunks": 3}],
        )

        response = client.get("/api/documents")

        assert response.status_code == 200
        assert response.json() == {"documents": [{"filename": "report.pdf", "chunks": 3}]}

    def test_returns_empty_list_when_no_documents(self, client, monkeypatch):
        monkeypatch.setattr(documents_router_module, "list_documents", lambda: [])

        response = client.get("/api/documents")

        assert response.status_code == 200
        assert response.json() == {"documents": []}


class TestDeleteDocument:
    def test_deleting_existing_document_returns_chunk_count(self, client, monkeypatch):
        monkeypatch.setattr(documents_router_module, "delete_document", lambda filename: 4)

        response = client.delete("/api/documents/report.pdf")

        assert response.status_code == 200
        assert response.json() == {"filename": "report.pdf", "chunks_deleted": 4}

    def test_deleting_nonexistent_document_returns_404(self, client, monkeypatch):
        monkeypatch.setattr(documents_router_module, "delete_document", lambda filename: 0)

        response = client.delete("/api/documents/missing.pdf")

        assert response.status_code == 404
        assert "missing.pdf" in response.json()["detail"]
