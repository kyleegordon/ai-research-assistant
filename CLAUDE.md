# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A fullstack RAG (retrieval-augmented generation) web app. Users upload PDFs and text files, ask questions, and receive answers grounded in the uploaded content with citations. Runs entirely on localhost — no cloud APIs, no deployment.

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite) |
| Backend | Python + FastAPI |
| Vector store | ChromaDB (in-process, no server) |
| LLM + embeddings | Ollama (local) |

## Repo layout

```
/frontend    React + TypeScript (Vite)
/backend     Python + FastAPI
```

## Dev commands

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload          # starts API at http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                        # starts UI at http://localhost:5173
npm run build                      # production build
```

### Ollama (must be running for LLM + embeddings)
```bash
ollama serve                       # starts Ollama daemon
ollama pull <model>                # pull a model before first use
```

## Architecture

The RAG pipeline has two phases:

**Ingestion** (triggered by file upload):
1. FastAPI receives the uploaded file
2. Document is chunked into passages
3. Each chunk is embedded via Ollama and stored in ChromaDB (in-process, persisted to disk)

**Query** (triggered by user question):
1. The question is embedded via Ollama
2. ChromaDB returns the top-k most similar chunks
3. The retrieved chunks + question are sent to Ollama as a prompt
4. The LLM response with source citations is streamed back to the frontend

ChromaDB runs embedded inside the FastAPI process — no separate database server. The collection persists to a local directory (e.g. `backend/chroma_db/`).

The frontend communicates with the backend exclusively over REST (file upload endpoint + query endpoint). Streaming responses use SSE or chunked transfer encoding.

## AI assistance boundaries

This project is intentionally used as a learning exercise. Respect these boundaries strictly.

**Do NOT generate — owner writes these manually:**
- Document chunking logic (chunk size, overlap, edge cases)
- Embedding pipeline (calling Ollama embeddings, storing in ChromaDB)
- Retrieval logic (top-K search, scoring, ranking)
- Prompt construction (injecting chunks, context length management)
- Streaming response handling (SSE: Ollama → FastAPI → React)

If asked to implement any of the above, explain the concepts and tradeoffs instead and let the owner write the code.

**AI assistance is fine for:**
- FastAPI boilerplate and route scaffolding
- React component scaffolding and file structure
- Vite/TypeScript config and environment setup
- CSS styling and layout
- Tests (once the core logic is written)
