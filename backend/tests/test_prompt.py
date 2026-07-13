"""Tests for services/prompt.py: build_prompt().

build_prompt is pure string formatting with no I/O. MAX_PROMPT_TOKENS is
monkeypatched in tests that need to force specific trim/drop behavior,
since chunks here are deliberately small relative to the real default budget.
"""
from typing import Optional

import services.prompt as prompt_module
from services.prompt import build_prompt


def make_chunk(source: str, size: int = 300, page: Optional[int] = None) -> dict:
    chunk = {"text": "x" * size, "source": source}
    if page is not None:
        chunk["page"] = page
    return chunk


class TestEmptyChunks:
    def test_no_chunks_returns_refusal_with_the_question(self):
        result = build_prompt("What is the capital of France?", [])
        assert "no relevant context" in result.lower()
        assert "What is the capital of France?" in result


class TestChunkFormatting:
    def test_source_and_text_appear_in_prompt(self):
        chunk = make_chunk("geography.pdf", size=50)
        result = build_prompt("q", [chunk])
        assert "geography.pdf" in result
        assert "x" * 50 in result

    def test_page_number_included_when_present(self):
        chunk = make_chunk("geography.pdf", size=50, page=3)
        result = build_prompt("q", [chunk])
        assert "p. 3" in result

    def test_page_number_omitted_when_absent(self):
        chunk = make_chunk("geography.pdf", size=50)
        result = build_prompt("q", [chunk])
        assert ", p. " not in result


class TestInstructionAndExample:
    def test_citation_format_instruction_present(self):
        result = build_prompt("q", [make_chunk("a.pdf")])
        assert "(Source: <filename>)" in result

    def test_worked_example_present(self):
        result = build_prompt("q", [make_chunk("a.pdf")])
        assert "Paris is the capital of France." in result
        assert "(Source: geography.pdf)" in result

    def test_ends_with_answer_cue_for_the_real_question(self):
        # Uses a different question than the worked example's hardcoded
        # "capital of France" so the assertion can't accidentally match
        # the example instead of the real question block.
        result = build_prompt("What is the capital of Germany?", [make_chunk("a.pdf")])
        assert result.rstrip().endswith("Answer:")
        assert "Question: What is the capital of Germany?\nAnswer:" in result


class TestBudgetTrimming:
    def test_all_chunks_included_when_budget_is_generous(self):
        chunks = [make_chunk(f"doc{i}.pdf", size=200) for i in range(5)]
        result = build_prompt("q", chunks)
        for i in range(5):
            assert f"doc{i}.pdf" in result

    def test_lowest_ranked_chunks_dropped_when_budget_is_tight(self, monkeypatch):
        # Chunks are passed in best-first (highest relevance) order, so a
        # tight budget should keep the earliest ones and drop the tail.
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 500)
        chunks = [make_chunk(f"doc{i}.pdf", size=300) for i in range(5)]
        result = build_prompt("q", chunks)

        assert "doc0.pdf" in result
        assert "doc4.pdf" not in result  # budget exhausted before reaching it

    def test_returns_a_valid_prompt_not_none_when_trimmed(self, monkeypatch):
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 500)
        chunks = [make_chunk(f"doc{i}.pdf", size=300) for i in range(5)]
        result = build_prompt("q", chunks)
        assert isinstance(result, str)
        assert result.rstrip().endswith("Answer:")

    def test_falls_back_to_refusal_when_even_first_chunk_does_not_fit(self, monkeypatch):
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 1)
        chunks = [make_chunk("doc0.pdf", size=300)]
        result = build_prompt("q", chunks)
        assert "no relevant context" in result.lower()

    def test_refusal_wording_matches_the_empty_chunks_case(self, monkeypatch):
        # The "nothing fit the budget" path and the "zero chunks retrieved"
        # path should refuse with identical wording, not drift apart.
        monkeypatch.setattr(prompt_module, "MAX_PROMPT_TOKENS", 1)
        budget_exhausted = build_prompt("q", [make_chunk("doc0.pdf", size=300)])
        no_chunks = build_prompt("q", [])
        assert budget_exhausted == no_chunks
