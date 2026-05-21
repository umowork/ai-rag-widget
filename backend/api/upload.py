"""
Upload endpoints — PDF, DOCX, TXT, and raw text.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from main import limiter

from backend.api.auth import require_api_key

from models.schemas import UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Allowed MIME types for file uploads
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def get_engine():
    """Dependency: returns RAGEngine from main."""
    from main import rag_engine
    return rag_engine


def _validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    # Check extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. "
                   f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Check content-type if available
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        # Accept anyway; some clients send wrong content-type
        logger.warning("Unexpected content-type '%s' for file '%s'",
                       file.content_type, file.filename)


@router.post("/text", response_model=UploadResponse)
@limiter.limit("30/minute")
async def upload_text(
    request: Request,
    text: str = Form(..., min_length=1, max_length=100000),
    source: str = Form("manual"),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
    engine=Depends(get_engine),
    _key: None = Depends(require_api_key),
):
    """
    Upload raw text as a document.
    """
    try:
        chunks_added = engine.add_text(
            text=text,
            source=source,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        logger.info("Uploaded text (source=%s): %d chunks", source, chunks_added)
        return UploadResponse(
            status="ok",
            chunks_added=chunks_added,
            message=f"Добавлено {chunks_added} фрагментов из текста ({source}).",
        )
    except Exception as e:
        logger.exception("Text upload error")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/file", response_model=UploadResponse)
@limiter.limit("30/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    engine=Depends(get_engine),
    _key: None = Depends(require_api_key),
):
    """
    Upload a document file (PDF, DOCX, TXT, MD).
    """
    _validate_file(file)

    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Read content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)} MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        # Save to temp file and process
        ext = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            chunks_added = engine.add_file(tmp_path, source=file.filename)
        finally:
            os.unlink(tmp_path)

        logger.info("Uploaded file '%s': %d chunks", file.filename, chunks_added)
        return UploadResponse(
            status="ok",
            chunks_added=chunks_added,
            message=f"Файл '{file.filename}' обработан: {chunks_added} фрагментов.",
        )
    except Exception as e:
        logger.exception("File upload error")
        raise HTTPException(status_code=500, detail="Internal server error") from e


# Backward-compat: POST /upload/pdf → POST /upload/file
@router.post("/pdf", response_model=UploadResponse)
@limiter.limit("30/minute")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    engine=Depends(get_engine),
    _key: None = Depends(require_api_key),
):
    """Legacy: upload PDF file (delegates to /upload/file)."""
    return await upload_file(request=request, file=file, engine=engine)
