# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A fullstack RAG (retrieval-augmented generation) web app. Users upload PDFs and text files, ask questions, and receive answers grounded in the uploaded content with citations. Runs entirely on localhost — no cloud APIs, no deployment.

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript (Vite) + MUI (Material UI) |
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
npm install @mui/material @emotion/react @emotion/styled
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

## Issue tracking

Pending work is tracked in Linear (team: **Ai-research-assistant**, e.g. `AI-12`). When completing work tied to a Linear issue:
1. Move the issue to **Done** (or the appropriate status).
2. Add a comment linking the commit hash that resolved it.

Do this immediately after merging/pushing, before reporting the task complete — don't leave tickets stale in Backlog/In Progress once the code has landed.

## Frontend dev guidelines

### UI library
Use **MUI (Material UI)** for all UI components. Do not introduce other component libraries. Prefer MUI primitives (`Box`, `Stack`, `Typography`, `Button`, etc.) over raw HTML elements. Use the MUI `sx` prop for one-off style overrides; define a theme for global design tokens (colors, spacing, typography).

### React best practices
- **Components**: one component per file, named to match the filename. Keep components focused — if a component is doing more than one thing, split it.
- **Reusability (DRY)**: before writing a new component or utility function, check if one already exists. Any UI pattern used in more than one place must be extracted into a shared component under `frontend/src/components/`. Any logic used in more than one place must be extracted into a custom hook (`frontend/src/hooks/`) or utility (`frontend/src/utils/`).
- **Props over duplication**: pass data and callbacks as props rather than copy-pasting logic across components.
- **State**: keep state as close to where it's used as possible. Lift state only when two or more sibling components need it. Avoid global state unless clearly necessary.
- **No inline styles**: use the MUI `sx` prop or a theme — no `style={{}}` attributes, no raw CSS strings inline.
- **TypeScript**: all components and functions must be fully typed. No `any`; use explicit prop interfaces.
