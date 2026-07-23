# Write this yourself — core RAG component (chunking + embedding pipeline)
from pypdf import PdfReader
import ollama
import chromadb

from config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, CHROMA_PATH

BATCH_SIZE = 300
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def ingest_document(file_path: str, filename: str) -> dict:
    """
    1. Loads the file using pypdf for PDFs, open() for .txt
    2. Splits text into chunks based on chunks
    3. For each chunk, calls Ollama's embedding endpoint
    4. Stores each chunk + its embedding in ChromaDB with source metadata
    5. Returns a summary dict
    """


    # Load file and extract text chunks
    if filename.lower().endswith(".txt"):
        with open(file_path, encoding='utf-8') as file:
            text = file.read()
            chunks = chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=["\n\n", "\n", ". ", " ", ""])
            chunk_pages = [None] * len(chunks) # .txt has no page concept
    elif filename.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        chunks = []
        chunk_pages = []
        prev_page_text = ""

        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            original_page_text = page_text

            if page_text == "":
                continue 

            trimmed_tail = get_overlap_tail(prev_page_text, CHUNK_OVERLAP)
            if trimmed_tail:
                page_text = trimmed_tail + " " + page_text  # seed prior page's tail so a boundary-split fact survives

            page_chunks = chunk_text(page_text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=["\n\n", "\n", ". ", " ", ""])
            chunks.extend(page_chunks)
            chunk_pages.extend([page_num] * len(page_chunks))
            prev_page_text = original_page_text
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    if not chunks:
        return {"chunks_indexed": 0}

    # Convert text to embeddings
    ollama_client = ollama.Client(host=OLLAMA_BASE_URL)

    all_embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:(i+BATCH_SIZE)]
        response = ollama_client.embed(
            model=OLLAMA_EMBED_MODEL,
            input=batch
            )
        all_embeddings.extend(response['embeddings'])

    metadatas = []
    for i, chunk in enumerate(chunks):
        meta = {"source": filename, "chunk": i}
        if chunk_pages[i] is not None:
            meta["page"] = chunk_pages[i]        # omit key entirely for .txt — don't set it to None
        metadatas.append(meta)

    # Store embeddings in ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("all-my-documents")

    collection.add(
      documents=chunks,
      metadatas=metadatas,
      ids=[f"{filename}_chunk_{i}" for i, _ in enumerate(chunks)],
      embeddings=all_embeddings
    )                                                                                                                                                                                                                                                                                                                                                            

    return {"chunks_indexed": len(chunks)}

def trim_tail_to_word_boundary(text: str) -> str:
    space_idx = text.find(" ")
    return text[space_idx+1:] if space_idx != -1 else "" # trim to word boundary or drop if none found


def get_overlap_tail(source: str, chunk_overlap: int) -> str:
    # chunk_overlap=0 guard: -0 == 0 in Python, so source[-0:] returns the whole source and would duplicate all content
    tail = source[-chunk_overlap:] if chunk_overlap else ""
    return trim_tail_to_word_boundary(tail)


def chunk_text(text: str, chunk_size: int, chunk_overlap: int, separators: list[str]) -> list[str]:
    """
    Recursively splits text into chunks no larger than chunk_size.

    Tries each separator in order (most-to-least semantic: paragraph → sentence
    → word → character). Pieces that still exceed chunk_size after a split are
    recursed on with the next separator. Small pieces are merged into a buffer
    and flushed when the next piece would overflow it. The tail of each flushed
    chunk is seeded into the next buffer to create overlap between chunks.
    """
    results = []
    if len(text) < chunk_size: return [text]

    # All separators exhausted, return as-is
    if not separators: return [text]

    chunks = text.split(separators[0])

    # separator wasn't present, fall through to next one
    if len(chunks) == 1:
        return chunk_text(text, chunk_size, chunk_overlap, separators[1:])

    buffer = ""
    for chunk in chunks:
        if len(chunk) <= chunk_size:
            if len(buffer) + len(chunk) > chunk_size:
                results.append(buffer)
                trimmed_tail = get_overlap_tail(buffer, chunk_overlap)
                
                if trimmed_tail:
                    buffer = trimmed_tail + separators[0] + chunk  # reinsert the separator that split() removed
                else:
                    buffer = chunk  # nothing precedes chunk in this fresh buffer, no separator needed
            else:
                # Rejoin with the separator
                buffer = chunk if not buffer else buffer + separators[0] + chunk

        if len(chunk) > chunk_size:
            if buffer:
                results.append(buffer)
                buffer = get_overlap_tail(buffer, chunk_overlap)
            results.extend(chunk_text(chunk, chunk_size, chunk_overlap, separators[1:]))

    if buffer:
        results.append(buffer)

    return results