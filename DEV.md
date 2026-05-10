# ──────────────────────────────────────────────────────
# AI RAG Widget — Development Guide
# ──────────────────────────────────────────────────────

## Quick Start

```bash
# 1. Enter project
cd 06-ai-rag-widget

# 2. Backend
cp .env.example .env
# Edit .env — set OPENAI_API_KEY or MOCK_MODE=true
make install
make test
make run          # → http://localhost:8000/docs

# 3. Admin UI (Next.js 15)
cd admin
npm install --no-bin-links
node node_modules/next/dist/bin/next build
# Static export in admin/dist/
```

## Project Structure

```
06-ai-rag-widget/
├── backend/                # FastAPI application
│   ├── main.py             # App factory + entry point
│   ├── config.py           # Environment configuration
│   ├── rag_engine.py       # Central RAG coordinator
│   ├── llm.py              # LLM Gateway (observability + fallback)
│   ├── logging_config.py   # structlog JSON logging
│   ├── api/                # Route handlers
│   ├── models/             # Pydantic schemas
│   └── services/           # Business logic
├── admin/                  # Next.js 15 + Tailwind admin panel
│   ├── app/page.tsx        # Upload + docs + embed code
│   └── package.json
├── widget/                 # Embeddable JS widget
│   └── widget.js
├── tests/                  # Test suite
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── .env.example
```

## Architecture

```
User → FastAPI → RAGEngine → VectorStoreService (ChromaDB)
                 ↓
            LLMGateway → LLMService (OpenAI / YandexGPT / Mock)
                 ↓
            Response ← Generated Answer + Sources

Document Upload → DocumentProcessor → TextSplitter → VectorStoreService
```

## Key Design Decisions

### LLM Gateway
All LLM calls route through `backend/llm.py` LLMGateway with:
- Structured logging (structlog JSON)
- Latency tracking
- Fallback to mock on failure

### structlog JSON Logging
Production logs are structured JSON. Debug mode uses colored console output.

### Lazy Imports
- `torch`, `sentence-transformers` → loaded only on first embed/rerank.
- `chromadb` → loaded only on first vector store operation.
- `openai` → loaded only on first LLM/embedding call.

### Embedding Model
Default: `intfloat/multilingual-e5-large` (HuggingFace).
Override via `EMBEDDING_MODEL` env var.

## API Endpoints

| Method | Path              | Description                        |
|--------|-------------------|------------------------------------|
| GET    | /health           | Service health + metadata          |
| POST   | /chat             | Synchronous Q&A                    |
| GET    | /chat/stream      | Streaming Q&A (SSE, real LLM)      |
| POST   | /upload/text      | Upload raw text                    |
| POST   | /upload/file      | Upload file (PDF/DOCX/TXT/MD)      |
| GET    | /widget.js        | Embeddable JS widget               |

## Environment Variables

See `.env.example` for complete list.

Key variables:
- `LLM_PROVIDER` — openai / yandexgpt / mock
- `EMBEDDING_MODEL` — default: intfloat/multilingual-e5-large
- `MOCK_MODE=true` — uses mock LLM (no API key)
- `CHROMA_DB_DIR` — ChromaDB persistence directory

## Testing

```bash
make test        # Run all tests
make test-v      # Verbose output
make test-cov    # With coverage report
```

## Docker

```bash
make docker-build  # docker compose build
make docker-up     # docker compose up -d
make docker-down   # docker compose down
```

## Admin UI

```bash
cd admin
npm install --no-bin-links
node node_modules/next/dist/bin/next build
# Export goes to admin/dist/
```

## License

MIT — built with AI assistance for portfolio showcase.
