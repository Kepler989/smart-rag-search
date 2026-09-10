# Smart RAG Document Search Assistant 🔍

A production-grade, full-stack **Retrieval-Augmented Generation (RAG)** document search system built for a developer portfolio. Upload PDFs, Markdown, and text files, then ask questions and get cited AI answers powered by **Google Gemini 2.5 Flash**.

## ✨ Features

- **Document Ingestion** — PDF, Markdown, and TXT support with recursive character text splitting (chunk size 1000, overlap 150)
- **Semantic Search** — pgvector HNSW cosine similarity index for sub-millisecond retrieval
- **RAG Pipeline** — Query → Embed → Vector Search → Gemini 2.5 Flash → Cited Answer
- **Streaming Responses** — Server-Sent Events for token-by-token streaming
- **Redis Caching** — SHA-256 keyed cache for embeddings and full LLM responses
- **Latency Tracking** — Per-request headers: `X-Embedding-Latency-Ms`, `X-Vector-Search-Latency-Ms`, `X-LLM-Latency-Ms`
- **Source Citations** — Every AI response includes page numbers and section references

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js Frontend (Port 3000)                  │
│  DocumentUploader · ChatInterface · SourceCitationPanel          │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST + SSE
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend (Port 8000)                    │
│  /api/v1/documents/upload  ·  /api/v1/query/  ·  /api/v1/query/stream │
├──────────────────┬──────────────────────┬────────────────────────┤
│   Ingestion      │   RAG Engine         │   Caching              │
│   PDF/MD/TXT     │   Gemini 2.5 Flash   │   Redis                │
│   Text Splitter  │   Prompt Builder     │   SHA-256 keys         │
└──────────────────┴──────────┬───────────┴────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│             PostgreSQL + pgvector (Port 5432)                    │
│  documents table · document_chunks table                         │
│  HNSW index (m=16, ef_construction=64) · cosine similarity       │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (running)
- Python 3.11+
- Node.js 18+
- Google API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd smart-rag-search

# Copy and fill in environment variables
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_actual_key

cp backend/.env.example backend/.env
# Edit backend/.env and set GOOGLE_API_KEY=your_actual_key
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL + pgvector, Redis, pgAdmin
docker compose up -d

# Verify services are healthy
docker compose ps
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies (already done if scaffolded)
npm install

# Start the dev server
npm run dev
```

### 5. Access the Application

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **pgAdmin** | http://localhost:5050 |
| **Health Check** | http://localhost:8000/health |

## 📁 Project Structure

```
smart-rag-search/
├── docker-compose.yml          # Infrastructure services
├── .env.example                # Root env template
├── scripts/
│   └── init_db.sql             # pgvector extension init
│
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial.py  # DB schema + HNSW index
│   └── app/
│       ├── main.py             # FastAPI entrypoint
│       ├── config.py           # Pydantic Settings
│       ├── database.py         # Async SQLAlchemy
│       ├── models/
│       │   ├── document.py     # Document ORM model
│       │   └── chunk.py        # DocumentChunk + Vector column
│       ├── schemas/
│       │   ├── document.py     # Document Pydantic schemas
│       │   └── query.py        # RAG request/response schemas
│       ├── services/
│       │   ├── cache.py        # Redis caching
│       │   ├── embedding.py    # Gemini text-embedding-004
│       │   ├── ingestion.py    # PDF/MD/TXT parsing + chunking
│       │   ├── vector_store.py # pgvector similarity search
│       │   └── rag_engine.py   # Prompt builder + Gemini generation
│       ├── api/routes/
│       │   ├── documents.py    # Upload, list, get, delete
│       │   └── query.py        # RAG + streaming endpoints
│       ├── middleware/
│       │   └── latency.py      # Latency tracking headers
│       └── background/
│           └── tasks.py        # Async document processing
│
└── frontend/
    ├── app/
    │   ├── layout.tsx          # Root layout
    │   ├── globals.css         # Global styles
    │   └── page.tsx            # Main page
    ├── components/
    │   ├── ChatInterface.tsx   # Full chat UI
    │   ├── MessageBubble.tsx   # Chat messages
    │   ├── DocumentUploader.tsx # Drag-and-drop upload
    │   ├── DocumentList.tsx    # Document sidebar
    │   ├── SourceCitationPanel.tsx # Collapsible citations
    │   └── LatencyBadge.tsx    # Latency metric pills
    ├── hooks/
    │   ├── useChat.ts          # Chat state + streaming
    │   └── useDocuments.ts     # Document list + polling
    └── lib/
        ├── api.ts              # Typed API client
        └── types.ts            # TypeScript types
```

## 🔧 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload PDF/MD/TXT |
| `GET` | `/api/v1/documents/` | List all documents |
| `GET` | `/api/v1/documents/{id}` | Get document by ID |
| `DELETE` | `/api/v1/documents/{id}` | Delete document |
| `POST` | `/api/v1/query/` | RAG query (cached) |
| `POST` | `/api/v1/query/stream` | RAG streaming (SSE) |
| `GET` | `/health` | Health check |

## ⚡ Response Headers

Every query response includes:
- `X-Embedding-Latency-Ms` — Gemini embedding time
- `X-Vector-Search-Latency-Ms` — pgvector HNSW search time
- `X-LLM-Latency-Ms` — Gemini generation time
- `X-Total-Latency-Ms` — End-to-end request time

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Lucide Icons |
| Backend | FastAPI, Uvicorn, Python 3.11 |
| Database | PostgreSQL 16 + pgvector |
| Vector Index | HNSW (cosine similarity) |
| AI Models | Gemini `text-embedding-004` + `gemini-2.5-flash` |
| Caching | Redis 7 |
| ORM | SQLAlchemy (async) + Alembic |
| Background Tasks | FastAPI BackgroundTasks |
