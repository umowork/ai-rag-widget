"""
Ingest module — document ingestion pipeline.

Coordinates loading, chunking, embedding, and storing documents.
Provides a clean API for both file uploads and raw text ingestion.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import structlog

from rag_engine import RAGEngine

logger = structlog.get_logger()


class IngestPipeline:
    """
    High-level ingestion pipeline.

    Usage:
        pipeline = IngestPipeline(rag_engine)
        count = pipeline.ingest_file("/path/to/doc.pdf")
        count = pipeline.ingest_text("Raw text content", source="manual")
    """

    def __init__(self, rag_engine: RAGEngine):
        self._rag_engine = rag_engine
        self._processor = rag_engine.document_processor

    def ingest_file(self, file_path: str, source: Optional[str] = None) -> int:
        """
        Ingest a single file into the vector store.

        Args:
            file_path: Path to PDF, DOCX, TXT, or MD file.
            source: Optional source label (defaults to filename).

        Returns:
            Number of chunks added.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        src = source or path.name
        logger.info("ingest_file_start", path=str(path), source=src)
        count = self._rag_engine.add_file(str(path), source=src)
        logger.info("ingest_file_done", path=str(path), chunks=count)
        return count

    def ingest_text(
        self,
        text: str,
        source: str = "manual",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> int:
        """
        Ingest raw text into the vector store.

        Args:
            text: Raw text content.
            source: Source label.
            chunk_size: Max chunk size.
            chunk_overlap: Overlap between chunks.

        Returns:
            Number of chunks added.
        """
        logger.info("ingest_text_start", source=source, text_length=len(text))
        count = self._rag_engine.add_text(
            text,
            source=source,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        logger.info("ingest_text_done", source=source, chunks=count)
        return count

    def ingest_directory(
        self,
        directory: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> dict:
        """
        Ingest all supported files from a directory.

        Args:
            directory: Path to directory.
            extensions: List of extensions to include (default: .pdf, .docx, .txt, .md).
            recursive: Whether to scan subdirectories.

        Returns:
            Dict with stats: {"files": int, "chunks": int, "errors": int}.
        """
        if extensions is None:
            extensions = [".pdf", ".docx", ".txt", ".md"]

        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        pattern = "**/*" if recursive else "*"
        files = [f for f in dir_path.glob(pattern) if f.suffix.lower() in extensions]

        total_chunks = 0
        errors = 0
        processed = 0

        logger.info("ingest_directory_start", path=directory, files_found=len(files))

        for file_path in files:
            try:
                count = self.ingest_file(str(file_path))
                total_chunks += count
                processed += 1
            except Exception as exc:
                logger.error("ingest_file_failed", path=str(file_path), error=str(exc))
                errors += 1

        logger.info(
            "ingest_directory_done",
            path=directory,
            processed=processed,
            chunks=total_chunks,
            errors=errors,
        )
        return {"files": processed, "chunks": total_chunks, "errors": errors}


def get_ingest_pipeline() -> IngestPipeline:
    """Factory: returns IngestPipeline using global RAGEngine."""
    from main import rag_engine
    return IngestPipeline(rag_engine)
