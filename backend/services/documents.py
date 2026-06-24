import os
from collections import Counter

import chromadb

from config import CHROMA_PATH, UPLOAD_DIR


def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection("all-my-documents")


def list_documents() -> list[dict]:
    collection = _get_collection()

    result = collection.get(include=["metadatas"])
    counts = Counter(
        metadata["source"] for metadata in result["metadatas"] if metadata.get("source")
    )

    return [{"filename": filename, "chunks": count} for filename, count in counts.items()]


def delete_document(filename: str) -> int:
    collection = _get_collection()

    existing = collection.get(where={"source": filename}, include=[])
    if not existing["ids"]:
        return 0

    collection.delete(where={"source": filename})

    # Defense-in-depth: even though filenames are sanitized at upload time,
    # never let a path-traversal-shaped value escape UPLOAD_DIR here.
    safe_name = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    if os.path.exists(file_path):
        os.remove(file_path)

    return len(existing["ids"])
