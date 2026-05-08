# AI Research Assistant

A local RAG (retrieval-augmented generation) app. Upload PDFs or text files, ask questions, and get answers grounded in your documents with citations.

Runs entirely on your machine — no API keys, no cloud services, no cost.

## Stack

- **Frontend:** React + TypeScript (Vite)
- **Backend:** Python + FastAPI
- **Vector store:** ChromaDB (in-process)
- **LLM + embeddings:** Ollama (local)

## Prerequisites

- [Node.js](https://nodejs.org)
- Python 3.10+
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
