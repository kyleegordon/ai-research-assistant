# Write this yourself — core RAG component (vector search + ranking)


def retrieve_chunks(query: str, top_k: int = 5) -> list[dict]:
    """
    Steps to implement:
    1. Embed the query string via Ollama
    2. Query ChromaDB for the top_k most similar chunks
    3. Return a list of dicts with keys: text, source, score (and any other metadata)
    """
    raise NotImplementedError
