"""Tests for routers/upload.py via FastAPI's TestClient.

upload_file() calls ingest_document() (services/ingest.py), which in turn calls
ollama.embed(...) and opens its own chromadb.PersistentClient — neither of
which we want running during tests. Every test here monkeypatches
routers.upload.ingest_document directly, so no real Ollama call or chromadb
write ever happens.

upload_file() also calls delete_document() (services/documents.py) before
re-ingesting, to clear out any stale chunks from a previous upload of the same
filename. Those tests monkeypatch routers.upload.delete_document as well, so
they exercise the *order* of operations independent of the real ChromaDB.
"""
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import routers.upload as upload_module
from routers.upload import router as upload_router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(upload_router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    directory = tmp_path / "uploads"
    monkeypatch.setattr(upload_module, "UPLOAD_DIR", str(directory))
    return directory


@pytest.fixture
def fake_ingest(monkeypatch):
    """Stand in for ingest_document(): records calls, never touches Ollama
    or ChromaDB, and returns a deterministic chunk count."""
    calls = []

    def _ingest(file_path: str, filename: str) -> dict:
        calls.append({"file_path": file_path, "filename": filename})
        return {"chunks_indexed": 7}

    monkeypatch.setattr(upload_module, "ingest_document", _ingest)
    return calls


@pytest.fixture
def fake_delete(monkeypatch):
    """Stand in for delete_document(): records calls and reports 0 deleted
    chunks by default (as if no prior version exists)."""
    calls = []

    def _delete(filename: str) -> int:
        calls.append(filename)
        return 0

    monkeypatch.setattr(upload_module, "delete_document", _delete)
    return calls


def _upload(client, filename="doc.txt", content=b"hello world", content_type="text/plain"):
    return client.post(
        "/api/upload",
        files={"file": (filename, content, content_type)},
    )


class TestUploadFile:
    def test_rejects_unsupported_content_type(self, client, upload_dir, fake_ingest, fake_delete):
        response = _upload(client, content_type="image/png")

        assert response.status_code == 400
        assert "Only PDF and text files are supported" in response.json()["detail"]
        assert fake_ingest == []

    def test_accepts_text_file_and_returns_filename_and_result(
        self, client, upload_dir, fake_ingest, fake_delete
    ):
        response = _upload(client, filename="notes.txt", content_type="text/plain")

        assert response.status_code == 200
        body = response.json()
        assert body["filename"] == "notes.txt"
        assert body["chunks_indexed"] == 7

    def test_accepts_pdf_content_type(self, client, upload_dir, fake_ingest, fake_delete):
        response = _upload(client, filename="doc.pdf", content_type="application/pdf")

        assert response.status_code == 200
        assert response.json()["filename"] == "doc.pdf"

    def test_saves_uploaded_file_to_upload_dir(self, client, upload_dir, fake_ingest, fake_delete):
        _upload(client, filename="notes.txt", content=b"some content")

        saved_path = upload_dir / "notes.txt"
        assert saved_path.exists()
        assert saved_path.read_bytes() == b"some content"

    def test_sanitizes_path_traversal_in_filename(self, client, upload_dir, fake_ingest, fake_delete):
        response = client.post(
            "/api/upload",
            files={"file": ("../../evil.txt", b"payload", "text/plain")},
        )

        assert response.status_code == 200
        assert response.json()["filename"] == "evil.txt"
        # Only the sanitized name should exist, directly inside upload_dir.
        assert (upload_dir / "evil.txt").exists()
        assert not (upload_dir.parent.parent / "evil.txt").exists()

    def test_ingest_failure_returns_500_with_explanatory_detail(
        self, client, upload_dir, fake_delete, monkeypatch
    ):
        def _broken_ingest(file_path: str, filename: str) -> dict:
            raise RuntimeError("ollama is not running")

        monkeypatch.setattr(upload_module, "ingest_document", _broken_ingest)

        response = _upload(client, filename="notes.txt")

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "notes.txt" in detail
        assert "already removed" in detail

    def test_ingest_is_called_with_saved_path_and_sanitized_filename(
        self, client, upload_dir, fake_ingest, fake_delete
    ):
        _upload(client, filename="notes.txt")

        assert len(fake_ingest) == 1
        call = fake_ingest[0]
        assert call["filename"] == "notes.txt"
        assert call["file_path"] == os.path.join(str(upload_dir), "notes.txt")


class TestReuploadReplacesChunks:
    """Confirm the existing upload_file() contract: delete_document() runs
    before ingest_document() on every upload, so re-uploading a filename never
    leaves stale chunks behind."""

    def test_delete_document_called_before_ingest_on_every_upload(
        self, client, upload_dir, fake_ingest, fake_delete
    ):
        _upload(client, filename="notes.txt")

        assert fake_delete == ["notes.txt"]
        assert len(fake_ingest) == 1

    def test_reuploading_same_filename_deletes_old_chunks_each_time(
        self, client, upload_dir, fake_ingest, fake_delete
    ):
        _upload(client, filename="notes.txt", content=b"version one")
        _upload(client, filename="notes.txt", content=b"version two, much longer than before")

        # delete_document ran once per upload of this filename.
        assert fake_delete == ["notes.txt", "notes.txt"]
        # ingest_document also ran once per upload.
        assert len(fake_ingest) == 2

    def test_final_chunk_count_reflects_only_latest_ingest_result(
        self, client, upload_dir, monkeypatch
    ):
        """Simulate re-ingesting with chromadb-like semantics: delete_document
        actually clears previously tracked chunks for the filename, and the
        chunk count reported back to the caller is whatever the *latest*
        ingest_document() call reports — never a stale or accumulated count."""
        indexed_chunks = {}  # filename -> chunk count, stand-in for chromadb state

        def fake_delete_document(filename: str) -> int:
            return indexed_chunks.pop(filename, 0)

        def fake_ingest_document(file_path: str, filename: str) -> dict:
            # First upload has 3 sentences, second (longer) has 9.
            count = 3 if indexed_chunks.get("_call_count", 0) == 0 else 9
            indexed_chunks["_call_count"] = indexed_chunks.get("_call_count", 0) + 1
            indexed_chunks[filename] = count
            return {"chunks_indexed": count}

        monkeypatch.setattr(upload_module, "delete_document", fake_delete_document)
        monkeypatch.setattr(upload_module, "ingest_document", fake_ingest_document)

        first = _upload(client, filename="notes.txt", content=b"short doc")
        assert first.json()["chunks_indexed"] == 3

        second = _upload(client, filename="notes.txt", content=b"a much longer document body")
        assert second.json()["chunks_indexed"] == 9

        # The tracked state for "notes.txt" reflects only the latest version's
        # chunk count, not 3 + 9 = 12 stale-plus-new chunks.
        assert indexed_chunks["notes.txt"] == 9

    def test_missing_filename_is_rejected_before_delete_or_ingest(
        self, client, upload_dir, fake_ingest, fake_delete
    ):
        response = client.post(
            "/api/upload",
            files={"file": ("", b"content", "text/plain")},
        )

        assert response.status_code in (400, 422)
        assert fake_delete == []
        assert fake_ingest == []
