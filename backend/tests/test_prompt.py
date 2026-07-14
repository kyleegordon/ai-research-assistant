"""Tests for services/prompt.py: build_prompt() and trim_history().

build_prompt is pure formatting/budgeting logic with no I/O. MAX_PROMPT_TOKENS
and MAX_HISTORY_TOKENS/MAX_HISTORY_TURNS are monkeypatched in tests that need
to force specific trim/drop behavior, since chunks and history here are
deliberately small relative to the real default budgets.

build_prompt now returns a list[dict] of chat messages ({"role", "content"})
rather than a single formatted string, so assertions search across the
combined content of all messages unless a test cares about which specific
message something appears in.
"""
from typing import Optional

import services.prompt as prompt_module
from services.prompt import build_prompt, trim_history
from routers.query import Message


def make_chunk(source: str, size: int = 300, page: Optional[int] = None) -> dict:
    chunk = {"text": "x" * size, "source": source}
    if page is not None:
        chunk["page"] = page
    return chunk


def combined_content(messages: list[dict]) -> str:
    return " ".join(m["content"] for m in messages)


class TestMessageStructure:
    def test_every_message_has_role_and_content_keys_only(self):
        result = build_prompt("q", [make_chunk("a.pdf")])
        for m in result:
            assert set(m.keys()) == {"role", "content"}

    def test_first_message_is_the_system_instruction(self):
        result = build_prompt("q", [make_chunk("a.pdf")])
        assert result[0]["role"] == "system"

    def test_last_message_is_the_current_user_turn(self):
        result = build_prompt("What is the capital of Germany?", [make_chunk("a.pdf")])
        assert result[-1]["role"] == "user"
        assert "Question: What is the capital of Germany?" in result[-1]["content"]


class TestEmptyChunks:
    def test_no_chunks_returns_refusal_with_the_question(self):
        result = build_prompt("What is the capital of France?", [])
        content = combined_content(result)
        assert "no relevant context" in content.lower()
        assert "What is the capital of France?" in content

    def test_no_chunks_refusal_is_a_user_message(self):
        result = build_prompt("q", [])
        assert result[-1]["role"] == "user"


class TestChunkFormatting:
    def test_source_and_text_appear_in_prompt(self):
        chunk = make_chunk("geography.pdf", size=50)
        result = build_prompt("q", [chunk])
        content = combined_content(result)
        assert "geography.pdf" in content
        assert "x" * 50 in content

    def test_page_number_included_when_present(self):
        chunk = make_chunk("geography.pdf", size=50, page=3)
        result = build_prompt("q", [chunk])
        assert "p. 3" in combined_content(result)

    def test_page_number_omitted_when_absent(self):
        chunk = make_chunk("geography.pdf", size=50)
        result = build_prompt("q", [chunk])
        assert ", p. " not in combined_content(result)


class TestInstructionAndExample:
    def test_citation_format_instruction_present(self):
        result = build_prompt("q", [make_chunk("a.pdf")])
        assert "(Source: <filename>)" in result[0]["content"]

    def test_worked_example_present(self):
        result = build_prompt("q", [make_chunk("a.pdf")])
        assert "Paris is the capital of France." in result[0]["content"]
        assert "(Source: geography.pdf)" in result[0]["content"]


class TestBudgetTrimming:
    def test_all_chunks_included_when_budget_is_generous(self):
        chunks = [make_chunk(f"doc{i}.pdf", size=200) for i in range(5)]
        result = build_prompt("q", chunks)
        content = combined_content(result)
        for i in range(5):
            assert f"doc{i}.pdf" in content

    def test_lowest_ranked_chunks_dropped_when_budget_is_tight(self, monkeypatch):
        # Chunks are passed in best-first (highest relevance) order, so a
        # tight budget should keep the earliest ones and drop the tail.
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 500)
        chunks = [make_chunk(f"doc{i}.pdf", size=300) for i in range(5)]
        result = build_prompt("q", chunks)
        content = combined_content(result)

        assert "doc0.pdf" in content
        assert "doc4.pdf" not in content  # budget exhausted before reaching it

    def test_returns_a_well_formed_message_list_when_trimmed(self, monkeypatch):
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 500)
        chunks = [make_chunk(f"doc{i}.pdf", size=300) for i in range(5)]
        result = build_prompt("q", chunks)
        assert isinstance(result, list)
        assert result[-1]["role"] == "user"
        assert "Question: q" in result[-1]["content"]

    def test_falls_back_to_refusal_when_even_first_chunk_does_not_fit(self, monkeypatch):
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 1)
        chunks = [make_chunk("doc0.pdf", size=300)]
        result = build_prompt("q", chunks)
        assert "no relevant context" in combined_content(result).lower()

    def test_refusal_wording_matches_the_empty_chunks_case(self, monkeypatch):
        # The "nothing fit the budget" path and the "zero chunks retrieved"
        # path should refuse with identical wording, not drift apart.
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 1)
        budget_exhausted = build_prompt("q", [make_chunk("doc0.pdf", size=300)])
        no_chunks = build_prompt("q", [])
        assert budget_exhausted == no_chunks

    def test_long_question_leaves_less_room_for_chunks(self, monkeypatch):
        # Regression test: the chunk budget must reserve room for the question
        # itself, not just the system instruction — otherwise a long question
        # plus a fully-packed chunk budget can exceed MAX_PROMPT_TOKENS.
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 500)
        chunks = [make_chunk(f"doc{i}.pdf", size=300) for i in range(5)]

        short_result = build_prompt("q", chunks)
        long_result = build_prompt("q " * 300, chunks)

        short_chunk_count = sum(1 for i in range(5) if f"doc{i}.pdf" in combined_content(short_result))
        long_chunk_count = sum(1 for i in range(5) if f"doc{i}.pdf" in combined_content(long_result))

        assert long_chunk_count < short_chunk_count


class TestHistory:
    def test_no_history_produces_no_extra_messages(self):
        result = build_prompt("q", [make_chunk("a.pdf")])
        # system message + current turn only
        assert len(result) == 2

    def test_history_messages_placed_between_system_and_current_turn(self):
        history = [
            Message(role="user", content="why is the sky blue?"),
            Message(role="assistant", content="Rayleigh scattering."),
        ]
        result = build_prompt("what about at sunset?", [make_chunk("a.pdf")], history)

        assert result[0]["role"] == "system"
        assert result[1] == {"role": "user", "content": "why is the sky blue?"}
        assert result[2] == {"role": "assistant", "content": "Rayleigh scattering."}
        assert result[-1]["role"] == "user"

    def test_history_included_in_no_context_path(self):
        history = [Message(role="user", content="prior question")]
        result = build_prompt("q", [], history)
        assert {"role": "user", "content": "prior question"} in result

    def test_history_beyond_turn_cap_is_dropped_oldest_first(self):
        history = [
            Message(role="user" if i % 2 == 0 else "assistant", content=f"msg {i}")
            for i in range(2 * (prompt_module.MAX_HISTORY_TURNS + 5))
        ]
        result = build_prompt("q", [make_chunk("a.pdf")], history)
        history_messages = result[1:-1]

        assert len(history_messages) == prompt_module.MAX_HISTORY_TURNS
        assert history_messages[0]["content"] == f"msg {len(history) - prompt_module.MAX_HISTORY_TURNS}"
        assert history_messages[-1]["content"] == f"msg {len(history) - 1}"


class TestTrimHistory:
    def test_empty_history_returns_empty(self):
        kept, tokens_used = trim_history([], max_tokens=1000, max_turns=10)
        assert kept == []
        assert tokens_used == 0

    def test_turn_cap_keeps_most_recent(self):
        history = [Message(role="user" if i % 2 == 0 else "assistant", content=f"msg {i}") for i in range(20)]
        kept, _ = trim_history(history, max_tokens=10_000, max_turns=10)
        assert len(kept) == 10
        assert [m["content"] for m in kept] == [f"msg {i}" for i in range(10, 20)]

    def test_token_budget_stops_before_turn_cap_when_content_is_long(self):
        history = [
            Message(role="user" if i % 2 == 0 else "assistant", content="word " * 200)
            for i in range(20)
        ]
        kept, tokens_used = trim_history(history, max_tokens=1024, max_turns=10)
        assert len(kept) < 10
        assert tokens_used <= 1024

    def test_kept_entries_are_plain_dicts_not_the_original_objects(self):
        history = [Message(role="user", content="hi")]
        kept, _ = trim_history(history, max_tokens=1000, max_turns=10)
        assert kept == [{"role": "user", "content": "hi"}]
        assert isinstance(kept[0], dict)
