# Write this yourself — core RAG component (chunking + embedding pipeline)
from pypdf import PdfReader
import re
import ollama
import chromadb

from config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, CHROMA_PATH

def ingest_document(file_path: str, filename: str) -> dict:
    """
    1. Loads the file using pypdf for PDFs, open() for .txt
    2. Splits text into chunks based on sentences
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
    # TODO Upgrade to recursive chunking
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Convert text to embeddings
    ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
    embeddings_response = ollama_client.embed(
        model=OLLAMA_EMBED_MODEL,
        input=sentences
        )

    # Store embeddings in ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("all-my-documents")

    collection.add(
      documents=sentences,
      metadatas=[{"source": filename, "chunk": i} for i, _ in enumerate(sentences)],
      ids=[f"{filename}_chunk_{i}" for i, _ in enumerate(sentences)],
      embeddings=embeddings_response['embeddings']
    )                                                                                                                                                                                                                                                                                                                                                            

    return {"chunks_indexed": len(sentences)}
