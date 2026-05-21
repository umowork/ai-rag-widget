"""
Application configuration — loaded from environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Config:
    # ─── LLM ────────────────────────────────────────────────────────
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    yandexgpt_api_key: str = ""
    yandexgpt_folder_id: str = ""
    yandexgpt_model: str = "yandexgpt-lite"

    # ─── Embedding ─────────────────────────────────────────────────
    embedding_provider: str = "huggingface"
    embedding_model: str = "intfloat/multilingual-e5-large"
    openai_embedding_model: str = "text-embedding-ada-002"

    # ─── Vector Store ──────────────────────────────────────────────
    chroma_db_dir: str = "./chroma_db"
    chroma_collection: str = "rag_docs"

    # ─── Document Processing ───────────────────────────────────────
    chunk_size: int = 500
    chunk_overlap: int = 50

    # ─── Search ─────────────────────────────────────────────────────
    top_k: int = 4
    rerank: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ─── Cache ─────────────────────────────────────────────────────
    cache_ttl: int = 300
    cache_max_size: int = 128

    # ─── Mode ──────────────────────────────────────────────────────
    mock_mode: bool = False
    debug: bool = False

    # ─── Server ────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "*"

    version: str = "1.0.0"

    # ─── Uploads ───────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables with defaults."""

        def _bool(val: Optional[str], default: bool = False) -> bool:
            if val is None:
                return default
            return val.lower() in ("1", "true", "yes", "on")

        return cls(
            # LLM
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            yandexgpt_api_key=os.getenv("YANDEXGPT_API_KEY", ""),
            yandexgpt_folder_id=os.getenv("YANDEXGPT_FOLDER_ID", ""),
            yandexgpt_model=os.getenv("YANDEXGPT_MODEL", "yandexgpt-lite"),
            # Embedding
            embedding_provider=os.getenv("EMBEDDING_PROVIDER", "huggingface"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
            # Vector store
            chroma_db_dir=os.getenv("CHROMA_DB_DIR", "./chroma_db"),
            chroma_collection=os.getenv("CHROMA_COLLECTION", "rag_docs"),
            # Document processing
            chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
            # Search
            top_k=int(os.getenv("TOP_K", "4")),
            rerank=_bool(os.getenv("RERANK"), True),
            reranker_model=os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
            # Cache
            cache_ttl=int(os.getenv("CACHE_TTL", "300")),
            cache_max_size=int(os.getenv("CACHE_MAX_SIZE", "128")),
            # Mode
            mock_mode=_bool(os.getenv("MOCK_MODE"), False),
            debug=_bool(os.getenv("DEBUG"), False),
            # Server
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000"),
            # Version
            version=os.getenv("APP_VERSION", "1.0.0"),
            # Uploads
            upload_dir=os.getenv("UPLOAD_DIR", "./uploads"),
            max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")),
        )
