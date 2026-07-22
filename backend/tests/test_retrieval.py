"""Tests for services/retrieval.py: build_retrieval_query() and retrieve_chunks().

build_retrieval_query is pure string concatenation with no I/O, so no mocking
is needed.

retrieve_chunks() embeds via Ollama and queries ChromaDB, so tests monkeypatch
both: chromadb.PersistentClient is swapped for a client pointed at a throwaway
tmp_path collection (seeded directly with known embeddings), and ollama.Client
is swapped for a fake whose embed() returns a fixed, controllable query vector.
This lets tests control the exact distance ChromaDB computes between the query
and each chunk, without depending on which distance metric or embedding model
is configured beyond "lower score = more similar" (confirmed: this collection's
default space is squared L2).
"""
import chromadb
import pytest

import services.retrieval as retrieval_module
from routers.query import Message
from services.retrieval import build_retrieval_query, retrieve_chunks


class TestNoHistory:
    def test_empty_history_returns_question_unchanged(self):
        assert build_retrieval_query("why is the sky blue?", []) == "why is the sky blue?"


class TestSingleExchange:
    def test_last_exchange_is_prepended_to_the_question(self):
        history = [
            Message(role="user", content="why is the sky blue?"),
            Message(role="assistant", content="Rayleigh scattering."),
        ]
        result = build_retrieval_query("what about at sunset?", history)

        assert result == "why is the sky blue? Rayleigh scattering. what about at sunset?"


class TestMultiTurnHistory:
    def test_only_the_last_exchange_is_used_not_earlier_turns(self):
        history = [
            Message(role="user", content="why is the sky blue?"),
            Message(role="assistant", content="Rayleigh scattering."),
            Message(role="user", content="what about the ocean?"),
            Message(role="assistant", content="Also Rayleigh scattering."),
        ]
        result = build_retrieval_query("and clouds?", history)

        assert "sky blue" not in result
        assert "what about the ocean?" in result
        assert "Also Rayleigh scattering." in result
        assert "and clouds?" in result


class TestOddLengthHistory:
    def test_single_dangling_message_does_not_crash(self):
        history = [Message(role="user", content="only one message")]
        result = build_retrieval_query("follow up", history)

        assert result == "only one message follow up"


@pytest.fixture
def chroma_client(tmp_path, monkeypatch):
    """A real chromadb PersistentClient backed by a throwaway temp directory,
    substituted for the one retrieve_chunks() would normally open at
    CHROMA_PATH. Tests seed chunks directly via this client so ChromaDB
    computes real distances against a controlled query embedding."""
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma_db"))
    monkeypatch.setattr(retrieval_module.chromadb, "PersistentClient", lambda path: client)
    return client


@pytest.fixture
def fake_query_embedding(monkeypatch):
    """Swaps ollama.Client for a fake whose embed() always returns the given
    vector, so the query's embedding (and thus its distance to each seeded
    chunk) is fully controlled by the test."""
    def _use(embedding):
        class FakeOllamaClient:
            def embed(self, model, input):
                return {"embeddings": [embedding]}

        monkeypatch.setattr(retrieval_module.ollama, "Client", lambda host: FakeOllamaClient())

    return _use


class TestRetrieveChunksRelevanceFilter:
    def test_chunk_within_threshold_is_kept(self, chroma_client, fake_query_embedding, monkeypatch):
        monkeypatch.setattr(retrieval_module, "RELEVANCE_THRESHOLD", 1.0)
        fake_query_embedding([1.0, 0.0, 0.0])
        collection = chroma_client.get_or_create_collection("all-my-documents")
        collection.add(
            ids=["near"],
            documents=["relevant chunk"],
            metadatas=[{"source": "doc.pdf"}],
            embeddings=[[1.0, 0.0, 0.0]],  # identical to query -> distance 0.0
        )

        result = retrieve_chunks("anything", top_k=5)

        assert result == [{"text": "relevant chunk", "source": "doc.pdf", "score": 0.0}]

    def test_chunk_beyond_threshold_is_dropped(self, chroma_client, fake_query_embedding, monkeypatch):
        monkeypatch.setattr(retrieval_module, "RELEVANCE_THRESHOLD", 1.0)
        fake_query_embedding([1.0, 0.0, 0.0])
        collection = chroma_client.get_or_create_collection("all-my-documents")
        collection.add(
            ids=["far"],
            documents=["irrelevant chunk"],
            metadatas=[{"source": "doc.pdf"}],
            embeddings=[[-1.0, 0.0, 0.0]],  # squared L2 distance = 4.0, well past threshold
        )

        result = retrieve_chunks("anything", top_k=5)

        assert result == []

    def test_mixed_relevance_keeps_only_chunks_within_threshold(
        self, chroma_client, fake_query_embedding, monkeypatch
    ):
        monkeypatch.setattr(retrieval_module, "RELEVANCE_THRESHOLD", 1.0)
        fake_query_embedding([1.0, 0.0, 0.0])
        collection = chroma_client.get_or_create_collection("all-my-documents")
        collection.add(
            ids=["near", "far"],
            documents=["near chunk", "far chunk"],
            metadatas=[{"source": "doc.pdf"}, {"source": "doc.pdf"}],
            embeddings=[[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]],
        )

        result = retrieve_chunks("anything", top_k=5)

        assert [r["text"] for r in result] == ["near chunk"]

    def test_score_exactly_at_threshold_is_kept_not_dropped(
        self, chroma_client, fake_query_embedding, monkeypatch
    ):
        # Filter is `if score > RELEVANCE_THRESHOLD: continue` -- a chunk whose
        # score exactly equals the threshold should survive, not be dropped.
        monkeypatch.setattr(retrieval_module, "RELEVANCE_THRESHOLD", 1.0)
        fake_query_embedding([0.0, 0.0, 0.0])
        collection = chroma_client.get_or_create_collection("all-my-documents")
        collection.add(
            ids=["boundary"],
            documents=["boundary chunk"],
            metadatas=[{"source": "doc.pdf"}],
            embeddings=[[1.0, 0.0, 0.0]],  # squared L2 distance = 1.0 exactly
        )

        result = retrieve_chunks("anything", top_k=5)

        assert len(result) == 1
        assert result[0]["score"] == 1.0


class TestRetrieveChunksPageMetadata:
    def test_page_key_included_when_present_in_metadata(
        self, chroma_client, fake_query_embedding, monkeypatch
    ):
        monkeypatch.setattr(retrieval_module, "RELEVANCE_THRESHOLD", 1.0)
        fake_query_embedding([1.0, 0.0, 0.0])
        collection = chroma_client.get_or_create_collection("all-my-documents")
        collection.add(
            ids=["chunk"],
            documents=["chunk text"],
            metadatas=[{"source": "doc.pdf", "page": 3}],
            embeddings=[[1.0, 0.0, 0.0]],
        )

        result = retrieve_chunks("anything", top_k=5)

        assert result == [{"text": "chunk text", "source": "doc.pdf", "score": 0.0, "page": 3}]

    def test_page_key_omitted_when_absent_from_metadata(
        self, chroma_client, fake_query_embedding, monkeypatch
    ):
        # .txt chunks have no page concept, so ingest_document() never sets one
        monkeypatch.setattr(retrieval_module, "RELEVANCE_THRESHOLD", 1.0)
        fake_query_embedding([1.0, 0.0, 0.0])
        collection = chroma_client.get_or_create_collection("all-my-documents")
        collection.add(
            ids=["chunk"],
            documents=["chunk text"],
            metadatas=[{"source": "notes.txt"}],
            embeddings=[[1.0, 0.0, 0.0]],
        )

        result = retrieve_chunks("anything", top_k=5)

        assert result == [{"text": "chunk text", "source": "notes.txt", "score": 0.0}]
        assert "page" not in result[0]

    def test_multiple_chunks_can_mix_paged_and_unpaged_sources(
        self, chroma_client, fake_query_embedding, monkeypatch
    ):
        monkeypatch.setattr(retrieval_module, "RELEVANCE_THRESHOLD", 1.0)
        fake_query_embedding([1.0, 0.0, 0.0])
        collection = chroma_client.get_or_create_collection("all-my-documents")
        collection.add(
            ids=["pdf_chunk", "txt_chunk"],
            documents=["from a pdf", "from a txt file"],
            metadatas=[{"source": "doc.pdf", "page": 7}, {"source": "notes.txt"}],
            embeddings=[[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
        )

        result = retrieve_chunks("anything", top_k=5)

        by_source = {r["source"]: r for r in result}
        assert by_source["doc.pdf"]["page"] == 7
        assert "page" not in by_source["notes.txt"]
