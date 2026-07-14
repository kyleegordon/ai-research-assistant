"""Tests for services/retrieval.py: build_retrieval_query().

build_retrieval_query is pure string concatenation with no I/O, so no
mocking is needed. retrieve_chunks() itself (embeds via Ollama, queries
ChromaDB) isn't covered here — it has no test file yet, same as before this
diff; only the new history-condensation logic is in scope.
"""
from routers.query import Message
from services.retrieval import build_retrieval_query


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
