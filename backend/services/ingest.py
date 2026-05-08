# Write this yourself — core RAG component (chunking + embedding pipeline)


def ingest_document(file_path: str, filename: str) -> dict:
    """
    Steps to implement:
    1. Load the file (use pypdf for PDFs, open() for .txt)
    2. Split text into chunks (decide: chunk size, overlap, edge cases)
    3. For each chunk, call Ollama's embedding endpoint
    4. Store each chunk + its embedding in ChromaDB with source metadata
    5. Return a summary dict (e.g. {"chunks_indexed": n})
    """
    raise NotImplementedError
