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
    try:
        # Verify vector store is accessible
        from main import rag_engine
        if rag_engine is not None:
            store_size = state.get("vector_store_size", 0)
        else:
            store_size = 0
            status = "degraded"
    except Exception:
        status = "degraded"

    return HealthResponse(
        status=status,
        version=state.get("version", "0.2.0"),
        vector_store_size=state.get("vector_store_size", 0),
        embedding_model=state.get("embedding_model", ""),
        llm_provider=state.get("llm_provider", ""),
        mock_mode=state.get("mock_mode", False),
    )
