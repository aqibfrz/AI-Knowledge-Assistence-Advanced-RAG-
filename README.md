# AI Knowledge Assistant (Advanced RAG)

AI Knowledge Assistant is a full-stack Retrieval-Augmented Generation (RAG) app that lets you ingest PDFs, DOCX files, and web pages, then ask questions with source-grounded answers and citations.

## Features

- FastAPI backend with RAG pipeline and streaming chat responses (SSE)
- React + Vite frontend for ingestion, chat, and admin stats
- Document ingestion from:
  - PDF files
  - DOCX files
  - Web URLs
- FAISS vector store persistence for retrieval
- Citation-aware responses (`source`, `chunk_id`, `preview`, `score`)
- Session-based chat memory

## Tech Stack

- **Backend:** FastAPI, LangChain, Groq, FAISS, Hugging Face Embeddings
- **Frontend:** React, TypeScript, Vite

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI routes
│   │   ├── rag.py          # Vector store + retrieval
│   │   ├── ingestion.py    # PDF/DOCX/URL parsing
│   │   ├── memory.py       # Session memory
│   │   ├── schemas.py      # Request/response models
│   │   └── config.py       # Settings
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
└── README.md
```

## Prerequisites

- Python 3.10+ (recommended: 3.11)
- Node.js 18+
- npm 9+
- A Groq API key

## Environment Setup

Create a `.env` file inside `backend/`:

```env
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_PATH=./data/faiss_index
APP_NAME=AI Knowledge Assistant
```

> Note: The app setting is read as `groq_api_key` from environment variables (`GROQ_API_KEY`).

## Run Locally

### 1) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at: `http://localhost:8000`

### 2) Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

## API Overview

- `GET /health` - backend health check
- `POST /ingest/files` - upload `.pdf` / `.docx` files
- `POST /ingest/url` - ingest content from a URL
- `POST /chat` - non-streaming chat response
- `POST /chat/stream` - streaming chat tokens + citations (SSE)
- `GET /admin/stats` - document/chunk/session stats

## Usage Flow

1. Start backend and frontend.
2. Ingest knowledge via file upload or URL.
3. Ask questions in the chat panel.
4. Review source citations in the "Sources" section.

## Notes

- Do not commit secrets. Keep `.env` local.
- Initial embedding model download may take time.
- Vector store data is persisted to `data/` (ignored by git).

## License

Add your preferred license (MIT, Apache-2.0, etc.).
