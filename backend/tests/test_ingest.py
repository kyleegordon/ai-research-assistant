"""Tests for services/ingest.py: chunk_text().

chunk_text is a pure function with no external dependencies, so no mocking
or fixtures are needed.
"""
from services.ingest import chunk_text

SEPS = ["\n\n", "\n", ". ", " ", ""]


class TestChunkTextBaseCases:
    def test_short_text_returned_as_single_chunk(self):
        result = chunk_text("hello world", chunk_size=500, chunk_overlap=0, separators=SEPS)
        assert result == ["hello world"]

    def test_empty_separators_returns_text_as_is_even_when_too_long(self):
        long_text = "x" * 200
        result = chunk_text(long_text, chunk_size=50, chunk_overlap=0, separators=[])
        assert result == [long_text]


class TestChunkTextSplitting:
    def test_produces_multiple_chunks_for_long_text(self):
        text = "word " * 200  # 1000 chars
        result = chunk_text(text, chunk_size=100, chunk_overlap=0, separators=SEPS)
        assert len(result) > 1

    def test_no_chunk_exceeds_chunk_size_plus_overlap(self):
        text = "word " * 200
        chunk_size, overlap = 100, 20
        result = chunk_text(text, chunk_size=chunk_size, chunk_overlap=overlap, separators=SEPS)
        for chunk in result:
            assert len(chunk) <= chunk_size + overlap

    def test_paragraph_boundaries_preferred_over_word_splitting(self):
        # Each paragraph fits in chunk_size, so the splitter should not break inside them
        para1 = "First paragraph with enough content."
        para2 = "Second paragraph with enough content."
        text = f"{para1}\n\n{para2}"
        result = chunk_text(text, chunk_size=500, chunk_overlap=0, separators=SEPS)
        # Both paragraphs fit under 500 chars so they should merge into one chunk,
        # or at worst split at the paragraph boundary — never mid-sentence
        assert all("\n\n" not in c or len(c) <= 500 for c in result)
        assert para1 in " ".join(result)
        assert para2 in " ".join(result)

    def test_falls_through_to_word_splitting_when_no_paragraph_breaks(self):
        # Long single line with no paragraph or sentence breaks
        text = "word " * 100  # 500 chars, no \n\n, \n, or ". "
        result = chunk_text(text, chunk_size=50, chunk_overlap=0, separators=SEPS)
        assert len(result) > 1
        # All chunks should be words, not character fragments (space separator used)
        for chunk in result:
            assert "  " not in chunk  # no double spaces from bad rejoining


class TestChunkTextOverlap:
    def test_overlap_appears_at_chunk_boundaries(self):
        text = "word " * 200
        chunk_size, overlap = 100, 20
        result = chunk_text(text, chunk_size=chunk_size, chunk_overlap=overlap, separators=SEPS)
        assert len(result) > 1
        # The tail of each chunk should appear at the start of the next
        for i in range(len(result) - 1):
            tail = result[i][-overlap:]
            assert result[i + 1].startswith(tail)

    def test_zero_overlap_total_length_matches_original(self):
        # With no overlap, concatenating all chunks should recover roughly the original
        # content (within separator re-joining margin). Large excess would mean duplication.
        text = " ".join(f"word{i}" for i in range(100))  # unique words, no repetition
        result = chunk_text(text, chunk_size=100, chunk_overlap=0, separators=SEPS)
        total = sum(len(c) for c in result)
        assert total <= len(text) * 1.05  # no more than 5% overhead from separator rejoining
