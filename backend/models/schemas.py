"""
Pydantic models for request/response schemas.
All API data shapes are defined here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Source / Document ─────────────────────────────────────────────────


class DocumentMetadata(BaseModel):
    """Metadata attached to a document chunk."""

    source: str = "unknown"
    page: Optional[int] = None
    file_type: Optional[str] = None
    uploaded_at: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class SourceDocument(BaseModel):
    """A single retrieved source document with content snippet."""

    content: str = Field(..., description="Snippet of document content")
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    score: Optional[float] = Field(None, description="Similarity score")


# ─── Requests ─────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    """Payload for synchronous /chat endpoint."""

    query: str = Field(..., min_length=1, max_length=4096, description="User question")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of documents to retrieve")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped


class ChatRequest(QueryRequest):
    """Extended request with conversation history (future use)."""

    history: List[Dict[str, str]] = Field(default_factory=list)


class UploadTextRequest(BaseModel):
    """Payload for /upload/text."""

    text: str = Field(..., min_length=1, description="Document text content")
    source: str = Field(default="manual", description="Source label")
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)


class FileUploadResponse(BaseModel):
    """Response after uploading a file."""

    status: str = "ok"
    chunks_added: int = Field(..., ge=0)
    filename: str = ""
    file_type: str = ""


# ─── Responses ────────────────────────────────────────────────────────


class QueryResponse(BaseModel):
    """Response from /chat endpoint."""

    answer: str = Field(..., description="Generated answer text")
    sources: List[SourceDocument] = Field(default_factory=list)
    model_used: str = Field(default="", description="Which LLM produced the answer")
    processing_time_ms: Optional[float] = None


class UploadResponse(BaseModel):
    """Response from upload endpoints."""

    status: str = "ok"
    chunks_added: int = 0
    message: str = ""


class HealthResponse(BaseModel):
    """Response from /health."""

    status: str = "ok"
    version: str = "0.2.0"
    vector_store_size: int = 0
    embedding_model: str = ""
    llm_provider: str = ""
    mock_mode: bool = False


class ErrorResponse(BaseModel):
    """Standard error payload."""

    detail: str
    error_code: Optional[str] = None


# ─── Streaming ────────────────────────────────────────────────────────


class StreamingEvent(BaseModel):
    """SSE streaming event payload."""

    token: Optional[str] = None
    sources: Optional[List[SourceDocument]] = None
    done: bool = False
    error: Optional[str] = None
