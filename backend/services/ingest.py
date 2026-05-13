# Write this yourself — core RAG component (chunking + embedding pipeline)
from pypdf import PdfReader
import re
import ollama
import chromadb

def ingest_document(file_path: str, filename: str) -> dict:
    """
    1. Loads the file using pypdf for PDFs, open() for .txt
    2. Splits text into chunks based on sentences
    3. For each chunk, calls Ollama's embedding endpoint
    4. Stores each chunk + its embedding in ChromaDB with source metadata
    5. Returns a summary dict
    """

    # TODO Add text file logic

    # Load file and extract text
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text = text + page.extract_text()

    # Split text into chunks
    # TODO Upgrade to recursive chunking
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Convert text to embeddings
    embeddings_response = ollama.embed(
        model='nomic-embed-text',
        input=sentences
        )

    # Store embeddings in ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("all-my-documents")

    collection.add(
      documents=sentences,
      metadatas=[{"source": filename, "chunk": i} for i, _ in enumerate(sentences)],
      ids=[f"{filename}_chunk_{i}" for i, _ in enumerate(sentences)],
      embeddings=embeddings_response['embeddings']
    )                                                                                                                                                                                                                                                                                                                                                            

    return {"chunks_indexed": len(sentences)}
