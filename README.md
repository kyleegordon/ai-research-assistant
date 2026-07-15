# AI Research Assistant

A local RAG (retrieval-augmented generation) app. Upload PDFs or text files, ask questions, and get answers grounded in your documents with citations — including follow-up questions that build on earlier turns in the conversation.

Runs entirely on your machine — no API keys, no cloud services, no cost.

## Features

- **Grounded Q&A with citations** — answers are drawn only from your uploaded documents, with source citations, and a clear "I don't know" when the documents don't cover the question.
- **Follow-up questions** — retrieval and prompting take conversation history into account, so you can ask a question, then a follow-up, without repeating context.
- **Relevance filtering** — retrieved passages that are too dissimilar from the question are dropped before reaching the model, instead of padding out the context with weak matches.
- **Document management** — view and delete uploaded documents, not just add new ones.
- **Markdown-rendered answers** with a one-click copy button.

## Stack

- **Frontend:** React + TypeScript (Vite) + MUI (Material UI)
- **Backend:** Python + FastAPI
- **Vector store:** ChromaDB (in-process)
- **LLM + embeddings:** Ollama (local)

## Prerequisites

- [Node.js](https://nodejs.org)
- Python 3.9+
- [Ollama](https://ollama.com)

## Setup

**1. Pull Ollama models**
```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

**2. Backend**
```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Frontend**
```bash
cd frontend
npm install
```

## Configuration

Backend settings are read from `backend/.env` (see `backend/.env.example` for defaults):

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `llama3.2` | Chat/generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `OLLAMA_NUM_CTX` | `8192` | Context window size passed to Ollama |
| `CHROMA_PATH` | `./chroma_db` | Where the vector store persists to disk |
| `RELEVANCE_THRESHOLD` | `0.8` | Max distance score a retrieved chunk can have before it's dropped as irrelevant |

## Running the app

Start each in a separate terminal:

```bash
# Backend
cd backend && source .venv/bin/activate && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

Then open [http://localhost:5173](http://localhost:5173).

> Ollama runs automatically as a background service after installation. If it's not running, start it with `ollama serve`.

## Running tests

```bash
cd backend
source .venv/bin/activate
pytest
```
