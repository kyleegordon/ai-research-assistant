import os

from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = "./uploads"
MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
