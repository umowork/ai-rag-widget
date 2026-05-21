"""
Chat endpoints — synchronous and streaming.
Uses RAGEngine to retrieve context and LLM to generate answers.
"""

from __future__ import annotations

import time
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from main import limiter

from backend.api.auth import require_api_key

from models.schemas import (
    QueryRequest,
    QueryResponse,
    StreamingEvent,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


def get_engine():
    """Dependency: returns RAGEngine instance from main."""
    from main import rag_engine
    return rag_engine


def get_cache():
    """Dependency: returns cache from main."""
    from main import response_cache
    return response_cache


@router.post("", response_model=QueryResponse)
@limiter.limit("30/minute")
async def chat(
    fastapi_request: Request,
    request: QueryRequest,
    engine=Depends(get_engine),
    cache=Depends(get_cache),
    _key: None = Depends(require_api_key),
):
    """
    Synchronous chat: retrieve context + generate LLM answer.

    Accepts JSON body with 'query' and optional 'top_k'.
    """
    start_time = time.time()

    try:
        result = engine.query(
            query=request.query,
            top_k=request.top_k,
            temperature=request.temperature,
            use_cache=True,
        )
    except Exception as e:
        logger.error("Chat error for query", query=request.query[:50], error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e

    elapsed = (time.time() - start_time) * 1000

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        model_used=result.get("model_used", ""),
        processing_time_ms=round(elapsed, 1),
    )


async def _stream_response(
    query: str,
    top_k: int,
    temperature: float | None,
    engine,
    cache,
) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream using real LLM streaming.
    Yields tokens as they arrive, then sources and done signal.
    """
    try:
        start_time = time.time()
        token_count = 0

        for chunk in engine.query_stream(
            query=query,
            top_k=top_k,
            temperature=temperature,
        ):
            if isinstance(chunk, str):
                token_count += 1
                event = StreamingEvent(token=chunk)
                yield f"data: {event.model_dump_json()}\n\n"
            elif isinstance(chunk, dict) and "__sources__" in chunk:
                sources = chunk["__sources__"]
                event = StreamingEvent(
                    sources=sources,
                    done=True,
                )
                yield f"data: {event.model_dump_json()}\n\n"

        elapsed = (time.time() - start_time) * 1000
        logger.debug("Stream complete", elapsed_ms=round(elapsed, 1), tokens=token_count)

    except Exception as e:
        logger.error("Stream error for query", query=query[:50], error=str(e))
        error_event = StreamingEvent(
            error=str(e),
            done=True,
        )
        yield f"data: {error_event.model_dump_json()}\n\n"


@router.get("/stream")
@limiter.limit("30/minute")
async def chat_stream(
    fastapi_request: Request,
    query: str = Query(..., min_length=1, max_length=4096),
    top_k: int = Query(default=4, ge=1, le=20),
    engine=Depends(get_engine),
    cache=Depends(get_cache),
    _key: None = Depends(require_api_key),
):
    """
    Streaming chat endpoint (SSE).
    Streams tokens one by one, then sources and done signal.
    """
    return StreamingResponse(
        _stream_response(query, top_k, None, engine, cache),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Backward-compatible GET /chat (non-streaming)
@router.get("")
@limiter.limit("30/minute")
async def chat_get(
    fastapi_request: Request,
    query: str = Query(..., min_length=1, max_length=4096),
    top_k: int = Query(default=4, ge=1, le=20),
    engine=Depends(get_engine),
    cache=Depends(get_cache),
    _key: None = Depends(require_api_key),
):
    """
    GET /chat — legacy endpoint, delegates to POST /chat logic.
    """
    result = engine.query(query=query, top_k=top_k, use_cache=True)
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        model_used=result.get("model_used", ""),
    )
