"""
AI RAG Widget — FastAPI application.

Modular RAG (Retrieval-Augmented Generation) service that:
  - Ingests documents (PDF, DOCX, TXT, MD, raw text)
  - Embeds chunks into ChromaDB vector store
  - Retrieves relevant context for user queries
  - Generates answers via LLM (OpenAI / YandexGPT / Mock)
  - Provides streaming SSE responses and an embeddable JS widget

Environment: use .env or environment variables.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Import config first — it has no heavy deps
from config import Config
from logging_config import setup_logging


# ─── Global State ───────────────────────────────────────────────────

app_state = {
    "version": "0.2.0",
    "vector_store_size": 0,
    "embedding_model": "",
    "llm_provider": "",
    "mock_mode": False,
}

# Lazy-init references set by create_app
rag_engine = None
response_cache = None
config_cache = None


# ─── Factory ────────────────────────────────────────────────────────


def create_app(config: Config) -> FastAPI:
    """
    Application factory. Creates and configures the FastAPI app.
    All heavy services are initialized lazily.
    """
    global rag_engine, response_cache, config_cache

    config_cache = config
    setup_logging(debug=config.debug)

    # ── FastAPI App ────────────────────────────────────────────────
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        logger = structlog.get_logger()
        logger.info("AI RAG Widget started")
        logger.info("  LLM provider", model=llm_service.model_name)
        logger.info("  Embedding model", model=embedding_service.model_name)
        logger.info("  Vector store", path=config.chroma_db_dir, doc_count=vector_store.count())
        logger.info("  Mock mode", enabled=config.mock_mode)
        logger.info("  Docs available", debug=config.debug)
        yield
        logger.info("AI RAG Widget shutting down")

    app = FastAPI(
        title="AI RAG Widget",
        version=app_state["version"],
        description="RAG-виджет для ответов по документам компании",
        docs_url="/docs" if config.debug else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────────────
    origins = [o.strip() for o in config.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Create upload dir ──────────────────────────────────────────
    os.makedirs(config.upload_dir, exist_ok=True)

    # ── Initialize Services (lazy where possible) ──────────────────
    from services.cache_service import ResponseCache
    from services.document_service import DocumentProcessor
    from services.embedding_service import (
        HuggingFaceEmbeddingService,
        MockEmbeddingService,
        create_embedding_service,
    )
    from services.reranker import RerankerService
    from services.vector_store import VectorStoreService

    # Determine effective provider
    effective_embedding_provider = config.embedding_provider

    # Embedding service
    if config.mock_mode:
        embedding_service = MockEmbeddingService()
    elif effective_embedding_provider == "openai":
        embedding_service = create_embedding_service(
            provider="openai",
            api_key=config.openai_api_key,
            model_name=config.openai_embedding_model,
        )
    else:
        # huggingface — lazy (sentence-transformers loaded on first embed)
        embedding_service = HuggingFaceEmbeddingService(
            model_name=config.embedding_model,
        )

    # Vector store (ChromaDB — lazy)
    vector_store = VectorStoreService(
        persist_directory=config.chroma_db_dir,
        embedding_service=embedding_service,
        collection_name=config.chroma_collection,
    )

    # LLM gateway (replaces direct llm_service creation)
    from llm import LLMGateway

    llm_service = LLMGateway.from_config(config)
    if config.mock_mode:
        logger = structlog.get_logger()
        logger.warning(
            "MOCK_MODE is ON — LLM responses are fake. "
            "Set LLM_PROVIDER=openai for real answers."
        )

    # Reranker (lazy — only loads on first rerank call)
    reranker = RerankerService(model_name=config.reranker_model) if config.rerank else None

    # Cache
    response_cache = ResponseCache(ttl_seconds=config.cache_ttl, max_size=config.cache_max_size)

    # Document processor
    doc_processor = DocumentProcessor(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    # RAG Engine
    from rag_engine import RAGEngine

    rag_engine = RAGEngine(
        vector_store=vector_store,
        embedding_service=embedding_service,
        llm_service=llm_service,
        document_processor=doc_processor,
        reranker=reranker,
        cache=response_cache,
        mock_mode=config.mock_mode,
    )

    # ── Update app state ───────────────────────────────────────────
    app_state["vector_store_size"] = vector_store.count()
    app_state["embedding_model"] = embedding_service.model_name
    app_state["llm_provider"] = llm_service.model_name
    app_state["mock_mode"] = config.mock_mode

    # ── Register Routers ───────────────────────────────────────────
    from api.health import router as health_router
    from api.chat import router as chat_router
    from api.upload import router as upload_router

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(upload_router)

    # ── Widget JS endpoint ─────────────────────────────────────────
    @app.get("/widget.js")
    async def widget_js():
        widget_path = Path(__file__).parent.parent / "widget" / "widget.js"
        if widget_path.exists():
            content = widget_path.read_text(encoding="utf-8")
        else:
            content = "console.warn('AI RAG Widget: widget.js not found.');"
        return HTMLResponse(content=content, media_type="application/javascript")

    return app


# ─── Entry Point ────────────────────────────────────────────────────

config = Config.from_env()
app = create_app(config)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )
