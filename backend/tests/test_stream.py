"""Tests for services/stream.py: stream_response().

stream_response() calls ollama.AsyncClient().chat(...) directly (it's the
function that owns that I/O), so tests monkeypatch ollama.AsyncClient itself,
as seen from services.stream's namespace, with a fake client that records
call args and yields configured chunks (or raises a configured exception)
instead of making a real Ollama call.

No pytest-asyncio dependency is added — each test drives the async generator
to completion with a small asyncio.run() helper instead.
"""
import asyncio

import pytest

import services.stream as stream_module
from services.stream import stream_response


def run_stream(messages: list[dict]) -> list[str]:
    async def _collect():
        return [event async for event in stream_response(messages)]

    return asyncio.run(_collect())


class FakeChunk:
    def __init__(self, content: str):
        self.message = type("FakeMessage", (), {"content": content})()


class FakeAsyncClient:
    """Configured per-test via the shared `state` dict from the fixture
    below, since stream_response() controls the constructor call site and
    can't be handed per-test args directly."""

    def __init__(self, state: dict, host=None):
        self._state = state
        state["host"] = host

    async def chat(self, model, messages, stream, options):
        self._state["chat_calls"].append(
            {"model": model, "messages": messages, "stream": stream, "options": options}
        )
        if self._state["error"]:
            raise self._state["error"]
        return self._chunks()

    async def _chunks(self):
        for token in self._state["tokens"]:
            yield FakeChunk(token)


@pytest.fixture
def fake_ollama_client(monkeypatch):
    state = {"tokens": [], "error": None, "host": None, "chat_calls": []}

    def _factory(host=None):
        return FakeAsyncClient(state, host=host)

    monkeypatch.setattr(stream_module.ollama, "AsyncClient", _factory)
    return state


class TestStreamedTokens:
    def test_yields_sse_formatted_tokens_for_each_chunk(self, fake_ollama_client):
        fake_ollama_client["tokens"] = ["Hello", " world"]

        events = run_stream([{"role": "user", "content": "hi"}])

        assert events == ["data: Hello\n\n", "data:  world\n\n", "data: [DONE]\n\n"]

    def test_yields_done_sentinel_after_all_tokens(self, fake_ollama_client):
        fake_ollama_client["tokens"] = ["one token"]

        events = run_stream([{"role": "user", "content": "hi"}])

        assert events[-1] == "data: [DONE]\n\n"

    def test_no_tokens_still_yields_done_sentinel(self, fake_ollama_client):
        fake_ollama_client["tokens"] = []

        events = run_stream([{"role": "user", "content": "hi"}])

        assert events == ["data: [DONE]\n\n"]


class TestChatCallArguments:
    def test_calls_chat_with_model_messages_and_num_ctx_option(self, fake_ollama_client):
        messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}]

        run_stream(messages)

        call = fake_ollama_client["chat_calls"][0]
        assert call["model"] == stream_module.OLLAMA_MODEL
        assert call["messages"] == messages
        assert call["stream"] is True
        assert call["options"] == {"num_ctx": stream_module.OLLAMA_NUM_CTX}

    def test_client_constructed_with_configured_base_url(self, fake_ollama_client):
        run_stream([{"role": "user", "content": "hi"}])

        assert fake_ollama_client["host"] == stream_module.OLLAMA_BASE_URL


class TestErrorHandling:
    def test_yields_error_event_when_chat_raises(self, fake_ollama_client):
        fake_ollama_client["error"] = RuntimeError("ollama is not running")

        events = run_stream([{"role": "user", "content": "hi"}])

        assert events == ["event: error\ndata: ollama is not running\n\n"]

    def test_no_done_sentinel_after_an_error(self, fake_ollama_client):
        fake_ollama_client["error"] = RuntimeError("boom")

        events = run_stream([{"role": "user", "content": "hi"}])

        assert "data: [DONE]\n\n" not in events
