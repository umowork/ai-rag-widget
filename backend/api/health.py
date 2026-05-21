"""
Health endpoint — service status and diagnostics.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from models.schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


def get_app_state():
    """
    Dependency: returns app state injected by main.
    Implemented as placeholder; overridden in main.py.
    """
    from main import app_state
    return app_state


@router.get("/health", response_model=HealthResponse)
async def health(state=Depends(get_app_state)):
    """
    Health check endpoint. Returns service status and metadata.
    """
    status = "ok"
    store_size = 0

    try:
        # Verify vector store is accessible by querying ChromaDB
        from main import rag_engine
        if rag_engine is not None and hasattr(rag_engine, "vector_store"):
            vs = rag_engine.vector_store
            try:
                store_size = vs.count()
            except Exception as exc:
                logger.warning("ChromaDB connectivity check failed: %s", exc)
                status = "degraded"
        else:
            store_size = 0
            status = "degraded"
    except Exception as exc:
        logger.warning("Health check: unable to access RAG engine: %s", exc)
        status = "degraded"

    return HealthResponse(
        status=status,
        version=state.get("version", "1.0.0"),
        vector_store_size=store_size,
        embedding_model=state.get("embedding_model", ""),
        llm_provider=state.get("llm_provider", ""),
        mock_mode=state.get("mock_mode", False),
    )
