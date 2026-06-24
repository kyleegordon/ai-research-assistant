"""Tests for routers/query.py via FastAPI's TestClient.

query() calls retrieve_chunks() (services/retrieval.py), which calls
ollama.embed(...) and queries chromadb, then build_prompt() (services/prompt.py),
then streams the result via stream_response() (services/stream.py), which calls
ollama.AsyncClient().generate(...). None of that should run for real in tests:
every test here monkeypatches routers.query.retrieve_chunks and
routers.query.stream_response directly. build_prompt() is pure string
formatting with no I/O, so it is left as-is.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import routers.query as query_module
from routers.query import router as query_router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(query_router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def fake_retrieve(monkeypatch):
    """Stand in for retrieve_chunks(): records calls, returns a fixed chunk
    list, never touches Ollama or ChromaDB."""
    calls = []

    def _retrieve(query: str, top_k: int = 3):
        calls.append({"query": query, "top_k": top_k})
        return [{"text": "Paris is the capital of France.", "source": "geo.txt", "score": 0.1}]

    monkeypatch.setattr(query_module, "retrieve_chunks", _retrieve)
    return calls


@pytest.fixture
def fake_stream(monkeypatch):
    """Stand in for stream_response(): records the prompt it was called with
    and yields a small deterministic SSE-shaped sequence, never touching
    Ollama's generate endpoint."""
    calls = []

    async def _stream(prompt: str):
        calls.append(prompt)
        yield "data: The capital of France is Paris.\n\n"
        yield "data: [DONE]\n\n"

    monkeypatch.setattr(query_module, "stream_response", _stream)
    return calls


class TestQuery:
    def test_returns_streamed_response_body(self, client, fake_retrieve, fake_stream):
        response = client.post("/api/query", json={"question": "What is the capital of France?"})

        assert response.status_code == 200
        assert "data: The capital of France is Paris.\n\n" in response.text
        assert "data: [DONE]\n\n" in response.text

    def test_response_media_type_is_event_stream(self, client, fake_retrieve, fake_stream):
        response = client.post("/api/query", json={"question": "anything"})

        assert response.headers["content-type"].startswith("text/event-stream")

    def test_default_top_k_is_five_when_not_specified(self, client, fake_retrieve, fake_stream):
        client.post("/api/query", json={"question": "anything"})

        assert fake_retrieve[0]["top_k"] == 5

    def test_custom_top_k_is_passed_through_to_retrieve_chunks(self, client, fake_retrieve, fake_stream):
        client.post("/api/query", json={"question": "anything", "top_k": 2})

        assert fake_retrieve[0]["top_k"] == 2

    def test_question_is_passed_through_to_retrieve_chunks(self, client, fake_retrieve, fake_stream):
        client.post("/api/query", json={"question": "What is the capital of France?"})

        assert fake_retrieve[0]["query"] == "What is the capital of France?"

    def test_retrieved_chunks_flow_into_the_prompt_sent_to_stream_response(
        self, client, fake_retrieve, fake_stream
    ):
        client.post("/api/query", json={"question": "What is the capital of France?"})

        assert len(fake_stream) == 1
        prompt = fake_stream[0]
        assert "Paris is the capital of France." in prompt
        assert "geo.txt" in prompt
        assert "What is the capital of France?" in prompt

    def test_missing_question_field_returns_422(self, client, fake_retrieve, fake_stream):
        response = client.post("/api/query", json={})

        assert response.status_code == 422
        assert fake_retrieve == []

    def test_empty_chunks_from_retrieval_still_produces_a_response(self, client, monkeypatch, fake_stream):
        monkeypatch.setattr(query_module, "retrieve_chunks", lambda query, top_k=3: [])

        response = client.post("/api/query", json={"question": "anything"})

        assert response.status_code == 200
        prompt = fake_stream[0]
        assert "no relevant context" in prompt
