"""Tests for services/ingest.py: chunk_text() and ingest_document().

chunk_text is a pure function with no external dependencies, so no mocking
or fixtures are needed.

ingest_document() does I/O (Ollama embeddings, ChromaDB, PdfReader), so its
tests monkeypatch all three: chromadb.PersistentClient is swapped for a
client pointed at a throwaway tmp_path collection, ollama.Client is swapped
for a fake with a fixed-length embed(), and PdfReader is swapped for a fake
built from a plain list of per-page text.
"""
import chromadb
import pytest

import services.ingest as ingest_module
from services.ingest import chunk_text, ingest_document

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

    def test_overlap_tail_never_starts_mid_word(self):
        # AI-29: chunk_overlap is a raw character count, so a naive tail slice
        # (buffer[-chunk_overlap:]) can land inside a word instead of on a space.
        # chunk_overlap here (5) is far smaller than the word, so if the tail
        # isn't snapped to a word boundary, some chunk will start with a bare
        # fragment like "docious" instead of the whole word or a space.
        word = "supercalifragilisticexpialidocious"
        text = f"{word} " * 20
        result = chunk_text(text, chunk_size=40, chunk_overlap=5, separators=[" ", ""])
        for chunk in result:
            stripped = chunk.lstrip()
            for cut in range(1, len(word)):
                fragment = word[cut:]
                assert not stripped.startswith(fragment) or stripped.startswith(word), (
                    f"chunk starts mid-word: {chunk!r}"
                )

    def test_overlap_window_with_no_space_falls_back_to_no_overlap(self):
        # When the overlap window is too small to contain any space (long
        # unbroken token, or a tiny chunk_overlap), there's no boundary to
        # snap to. The fix must fall back to dropping the tail rather than
        # raising (tail.index(" ") would throw if no space is present).
        text = ("supercalifragilisticexpialidocious " * 20)
        result = chunk_text(text, chunk_size=40, chunk_overlap=5, separators=[" ", ""])
        assert len(result) > 1

    def test_zero_overlap_does_not_raise(self):
        # chunk_overlap=0 -> tail is "" up front; a fix that unconditionally
        # calls tail.index(" ") without checking for "" first would raise
        # ValueError here instead of taking the existing no-overlap fallback.
        text = "word " * 200
        result = chunk_text(text, chunk_size=100, chunk_overlap=0, separators=SEPS)
        assert len(result) > 1


@pytest.fixture
def chroma_client(tmp_path, monkeypatch):
    """Real chromadb PersistentClient backed by a throwaway temp directory,
    substituted for the one ingest_document() would normally open at
    CHROMA_PATH."""
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma_db"))
    monkeypatch.setattr(ingest_module.chromadb, "PersistentClient", lambda path: client)
    return client


@pytest.fixture
def fake_embed(monkeypatch):
    """Swaps ollama.Client for a fake that returns one fixed-length embedding
    per input chunk, so ingest_document() never makes a real network call."""
    class FakeOllamaClient:
        def embed(self, model, input):
            return {"embeddings": [[0.0, 0.0, 0.0] for _ in input]}

    monkeypatch.setattr(ingest_module.ollama, "Client", lambda host: FakeOllamaClient())


@pytest.fixture
def fake_pdf_reader(monkeypatch):
    """Swaps PdfReader for a fake whose .pages are built from a plain list of
    raw page texts, so tests control extracted text per page without needing
    a real PDF file on disk."""
    def _use(page_texts):
        class FakePage:
            def __init__(self, text):
                self._text = text

            def extract_text(self):
                return self._text

        class FakeReader:
            def __init__(self, *_args, **_kwargs):
                self.pages = [FakePage(t) for t in page_texts]

        monkeypatch.setattr(ingest_module, "PdfReader", FakeReader)

    return _use


class TestIngestDocumentPageTracking:
    def test_txt_chunks_have_no_page_key(self, tmp_path, chroma_client, fake_embed):
        file_path = tmp_path / "notes.txt"
        file_path.write_text("Just some short plain text content.", encoding="utf-8")

        ingest_document(str(file_path), "notes.txt")

        stored = chroma_client.get_or_create_collection("all-my-documents").get()
        assert len(stored["ids"]) == 1
        assert stored["metadatas"][0]["source"] == "notes.txt"
        assert "page" not in stored["metadatas"][0]

    def test_pdf_chunks_are_tagged_with_their_source_page(
        self, tmp_path, chroma_client, fake_embed, fake_pdf_reader
    ):
        fake_pdf_reader(["Text from the first page.", "Text from the second page."])

        ingest_document(str(tmp_path / "doc.pdf"), "doc.pdf")

        stored = chroma_client.get_or_create_collection("all-my-documents").get()
        pages = {meta["page"] for meta in stored["metadatas"]}
        assert pages == {1, 2}
        # content unique to page 2 should be tagged page 2
        for doc, meta in zip(stored["documents"], stored["metadatas"]):
            if "second page" in doc:
                assert meta["page"] == 2
        # AI-31: page 2's chunk is expected to also carry a seeded tail from page
        # 1's text (so a fact split across the page boundary survives), so "first
        # page" text legitimately appears in a page == 2 chunk too
        page_2_docs = [doc for doc, meta in zip(stored["documents"], stored["metadatas"]) if meta["page"] == 2]
        assert any("first page" in doc for doc in page_2_docs)

    def test_blank_page_is_skipped_without_shifting_later_page_numbers(
        self, tmp_path, chroma_client, fake_embed, fake_pdf_reader
    ):
        # Middle page extracts to "" (e.g. a scanned/image-only page)
        fake_pdf_reader(["First page text.", "", "Third page text."])

        ingest_document(str(tmp_path / "doc.pdf"), "doc.pdf")

        stored = chroma_client.get_or_create_collection("all-my-documents").get()
        pages = {meta["page"] for meta in stored["metadatas"]}
        # page 2 produced no chunks and should not appear; page 3 keeps its real,
        # unshifted page number rather than being renumbered to 2
        assert pages == {1, 3}

    def test_all_pages_blank_returns_zero_chunks_without_storing_anything(
        self, tmp_path, chroma_client, fake_embed, fake_pdf_reader
    ):
        # Every page extracts to "" (e.g. a fully scanned/image-only PDF) ->
        # chunks ends up [] and ingest_document() should short-circuit before
        # ever calling collection.add() with empty documents/embeddings lists.
        fake_pdf_reader(["", ""])

        result = ingest_document(str(tmp_path / "doc.pdf"), "doc.pdf")

        assert result == {"chunks_indexed": 0}
        stored = chroma_client.get_or_create_collection("all-my-documents").get()
        assert stored["ids"] == []
