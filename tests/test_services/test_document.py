"""
Tests for DocumentProcessor and TextSplitter.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from services.document_service import DocumentProcessor, TextSplitter, ChunkedDocument


class TestTextSplitter:
    """Tests for the TextSplitter class."""

    def test_split_short_text(self, text_splitter):
        """Text shorter than chunk_size returns single chunk."""
        chunks = text_splitter.split_text("Короткий текст.")
        assert len(chunks) == 1
        assert chunks[0] == "Короткий текст."

    def test_split_long_text(self, text_splitter):
        """Text longer than chunk_size is split."""
        long = " ".join(["слово"] * 100)
        chunks = text_splitter.split_text(long)
        assert len(chunks) > 1

    def test_split_empty_text(self, text_splitter):
        """Empty text returns empty list."""
        chunks = text_splitter.split_text("")
        assert chunks == []

    def test_split_whitespace_only(self, text_splitter):
        """Whitespace-only text returns empty list."""
        chunks = text_splitter.split_text("   \n\n  ")
        assert chunks == []

    def test_chunk_overlap_less_than_size(self):
        """chunk_overlap must be less than chunk_size."""
        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            TextSplitter(chunk_size=100, chunk_overlap=100)

    def test_split_preserves_paragraphs(self):
        """Splitter respects paragraph boundaries."""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        text = (
            "Первый параграф содержит достаточно много текста для того чтобы "
            "превысить лимит размера чанка.\n\n"
            "Второй параграф с дополнительной информацией о компании и её услугах.\n\n"
            "Третий параграф с контактными данными и адресом офиса в центре города."
        )
        chunks = splitter.split_text(text)
        assert len(chunks) >= 2


class TestDocumentProcessor:
    """Tests for the DocumentProcessor class."""

    def test_load_txt_file(self, doc_processor, sample_txt_path):
        """Load and chunk a TXT file."""
        result = doc_processor.load_and_chunk(sample_txt_path)
        assert isinstance(result, ChunkedDocument)
        assert len(result) > 0
        assert result.metadata.source == "test_doc.txt"
        assert result.metadata.file_type == "txt"

    def test_load_text_from_upload_bytes(self, doc_processor):
        """Load text from uploaded bytes."""
        content = "Тестовый контент для загрузки через bytes.".encode("utf-8")
        result = doc_processor.load_text_from_upload(content, "test.txt")
        assert len(result) > 0
        assert result.metadata.source == "test.txt"

    def test_load_unsupported_extension(self, doc_processor):
        """Unsupported extension raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            doc_processor.load_and_chunk("/fake/file.xyz")

    def test_load_nonexistent_file(self, doc_processor):
        """Nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            doc_processor.load_and_chunk("/nonexistent/file.pdf")

    def test_chunk_text_direct(self, doc_processor):
        """Direct text chunking works."""
        result = doc_processor.chunk_text("Тестовый текст для разбиения на чанки.")
        assert isinstance(result, ChunkedDocument)
        assert len(result) > 0

    def test_chunk_texts_multiple(self, doc_processor):
        """Chunk multiple texts at once."""
        texts = ["Первый текст.", "Второй текст с дополнительной информацией."]
        result = doc_processor.chunk_texts(texts)
        assert len(result) >= 2

    def test_loaded_txt_metadata(self, doc_processor, sample_txt_path):
        """Loaded TXT has correct metadata."""
        result = doc_processor.load_and_chunk(sample_txt_path, metadata={"department": "legal"})
        assert result.metadata.source == "test_doc.txt"
        assert result.metadata.file_type == "txt"
        assert result.chunk_metadata[0].source == "test_doc.txt"
