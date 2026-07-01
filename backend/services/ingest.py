# Write this yourself — core RAG component (chunking + embedding pipeline)
from pypdf import PdfReader
import ollama
import chromadb

from config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, CHROMA_PATH

def ingest_document(file_path: str, filename: str) -> dict:
    """
    1. Loads the file using pypdf for PDFs, open() for .txt
    2. Splits text into chunks based on chunks
    3. For each chunk, calls Ollama's embedding endpoint
    4. Stores each chunk + its embedding in ChromaDB with source metadata
    5. Returns a summary dict
    """

    # Load file and extract text
    if filename.lower().endswith(".txt"):
        with open(file_path, encoding='utf-8') as file:
            text = file.read()
    elif filename.lower().endswith(".pdf"):
        reader = PdfReader(file_path)
        text = ""
        
        for page in reader.pages:
            text = text + page.extract_text()
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    # Split text into chunks
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ". ", " ", ""])

    # Convert text to embeddings
    ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
    embeddings_response = ollama_client.embed(
        model=OLLAMA_EMBED_MODEL,
        input=chunks
        )

    # Store embeddings in ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("all-my-documents")

    collection.add(
      documents=chunks,
      metadatas=[{"source": filename, "chunk": i} for i, _ in enumerate(chunks)],
      ids=[f"{filename}_chunk_{i}" for i, _ in enumerate(chunks)],
      embeddings=embeddings_response['embeddings']
    )                                                                                                                                                                                                                                                                                                                                                            

    return {"chunks_indexed": len(chunks)}


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
                # chunk_overlap=0 guard: -0 == 0 in Python, so buffer[-0:] returns the whole buffer and would duplicate all content
                buffer = (buffer[-chunk_overlap:] if chunk_overlap else "") + chunk
            else:
                # Rejoin with the separator
                buffer = chunk if not buffer else buffer + separators[0] + chunk

        if len(chunk) > chunk_size:
            if buffer:
                results.append(buffer)
                buffer = (buffer[-chunk_overlap:] if chunk_overlap else "")
            results.extend(chunk_text(chunk, chunk_size, chunk_overlap, separators[1:]))

    if buffer:
        results.append(buffer)

    return results