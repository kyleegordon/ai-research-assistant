"""Tests for services/documents.py: list_documents() and delete_document().

These both go through the module-level _get_collection(), which normally opens
chromadb.PersistentClient(path="./chroma_db") — a path relative to wherever the
process happens to be running from, and the same directory the real app uses.
Every test here monkeypatches _get_collection() to point at a fresh temporary
directory instead, so nothing ever touches backend/chroma_db.
"""
import os

import chromadb
import pytest

from services import documents as documents_module
from services.documents import list_documents, delete_document


@pytest.fixture
def collection(tmp_path, monkeypatch):
    """A chromadb collection backed by a throwaway temp directory, wired up as
    the return value of services.documents._get_collection()."""
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma_db"))
    coll = client.get_or_create_collection("all-my-documents")

    monkeypatch.setattr(documents_module, "_get_collection", lambda: coll)

    return coll


def _add_chunks(collection, filename: str, count: int, start: int = 0):
    ids = [f"{filename}_chunk_{i}" for i in range(start, start + count)]
    collection.add(
        ids=ids,
        documents=[f"{filename} chunk {i}" for i in range(start, start + count)],
        metadatas=[{"source": filename, "chunk": i} for i in range(start, start + count)],
        embeddings=[[0.1, 0.2, 0.3] for _ in range(count)],
    )


class TestListDocuments:
    def test_empty_collection_returns_empty_list(self, collection):
        assert list_documents() == []

    def test_single_document_reports_filename_and_chunk_count(self, collection):
        _add_chunks(collection, "report.pdf", count=3)

        result = list_documents()

        assert result == [{"filename": "report.pdf", "chunks": 3}]

    def test_multiple_documents_are_each_counted_independently(self, collection):
        _add_chunks(collection, "a.pdf", count=2)
        _add_chunks(collection, "b.txt", count=5)

        result = list_documents()

        by_filename = {entry["filename"]: entry["chunks"] for entry in result}
        assert by_filename == {"a.pdf": 2, "b.txt": 5}

    def test_chunks_missing_source_metadata_are_ignored(self, collection):
        collection.add(
            ids=["orphan_chunk_0"],
            documents=["no source here"],
            metadatas=[{"chunk": 0}],
            embeddings=[[0.1, 0.2, 0.3]],
        )

        assert list_documents() == []


class TestDeleteDocument:
    def test_deleting_existing_document_removes_its_chunks(self, collection):
        _add_chunks(collection, "report.pdf", count=4)

        deleted_count = delete_document("report.pdf")

        assert deleted_count == 4
        assert list_documents() == []

    def test_deleting_nonexistent_document_returns_zero(self, collection):
        deleted_count = delete_document("does-not-exist.pdf")

        assert deleted_count == 0

    def test_deleting_one_document_does_not_affect_others(self, collection):
        _add_chunks(collection, "keep.pdf", count=2)
        _add_chunks(collection, "remove.pdf", count=3)

        deleted_count = delete_document("remove.pdf")

        assert deleted_count == 3
        assert list_documents() == [{"filename": "keep.pdf", "chunks": 2}]

    def test_delete_removes_file_from_upload_dir_when_present(
        self, collection, tmp_path, monkeypatch
    ):
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        monkeypatch.setattr(documents_module, "UPLOAD_DIR", str(upload_dir))

        file_path = upload_dir / "report.pdf"
        file_path.write_text("dummy content")

        _add_chunks(collection, "report.pdf", count=1)

        delete_document("report.pdf")

        assert not file_path.exists()

    def test_delete_does_not_escape_upload_dir_via_path_traversal(
        self, collection, tmp_path, monkeypatch
    ):
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        monkeypatch.setattr(documents_module, "UPLOAD_DIR", str(upload_dir))

        # A file living "outside" the upload dir that a path-traversal-shaped
        # filename might otherwise be able to reach.
        outside_file = tmp_path / "secret.txt"
        outside_file.write_text("do not delete me")

        traversal_name = "../secret.txt"
        _add_chunks(collection, traversal_name, count=1)

        delete_document(traversal_name)

        assert outside_file.exists()

    def test_delete_with_no_matching_chunks_does_not_touch_upload_dir(
        self, collection, tmp_path, monkeypatch
    ):
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        monkeypatch.setattr(documents_module, "UPLOAD_DIR", str(upload_dir))

        file_path = upload_dir / "untouched.pdf"
        file_path.write_text("dummy content")

        deleted_count = delete_document("untouched.pdf")

        # No chunks existed for this filename, so delete_document should
        # short-circuit and never reach the filesystem removal step.
        assert deleted_count == 0
        assert file_path.exists()
