# Write this yourself — core RAG component (vector search + ranking)
import ollama
import chromadb

from config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, CHROMA_PATH, RELEVANCE_THRESHOLD

def build_retrieval_query(question: str, history: list) -> str:
    if not history:
        return question

    # last exchange only, most recent user+assistant pair.
    recent = history[-2:]
    context_str = " ".join(turn.content for turn in recent)

    return f"{context_str} {question}"

def retrieve_chunks(query: str, top_k: int = 3) -> list[dict]:
    """
    1. Embeds the query string via Ollama
    2. Queries ChromaDB for the top_k most similar chunks
    3. Returns a list of dicts filtered based on relevance score with keys: text, source, score (and any other metadata)
    """

    # Embed query string
    ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
    embeddings_response = ollama_client.embed(
    model=OLLAMA_EMBED_MODEL,
    input=[query]
    )

    # Query ChromaDB for similar chunks
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("all-my-documents")

    query_response = collection.query(
        query_embeddings=[embeddings_response['embeddings'][0]],
        n_results=top_k
        )

    results = []
    for text, source, score in zip(query_response['documents'][0], query_response['metadatas'][0], query_response['distances'][0]):
        if score > RELEVANCE_THRESHOLD:
            continue
        results.append({"text": text, "source": source['source'], "score": score})

    return results
