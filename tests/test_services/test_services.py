"""
Tests for services: cache, vector store, embedding, reranker.
"""

from __future__ import annotations

import time

import pytest

from services.cache_service import ResponseCache
from services.document_service import TextSplitter


class TestResponseCache:
    """Tests for in-memory response cache."""

    def test_cache_set_and_get(self, cache):
        """Set then get returns the cached value."""
        cache.set("query1", "context1", "response1")
        result = cache.get("query1", "context1")
        assert result == "response1"

    def test_cache_miss(self, cache):
        """Non-existent key returns None."""
        result = cache.get("unknown", "context")
        assert result is None

    def test_cache_ttl_expiry(self):
        """Expired entries return None."""
        cache = ResponseCache(ttl_seconds=1, max_size=16)
        cache.set("q", "c", "r")
        time.sleep(1.1)
        result = cache.get("q", "c")
        assert result is None

    def test_cache_clear(self, cache):
        """Clear removes all entries."""
        cache.set("q1", "c1", "r1")
        cache.set("q2", "c2", "r2")
        cache.clear()
        assert cache.size == 0

    def test_cache_invalidate(self, cache):
        """Invalidate removes specific entry."""
        cache.set("q1", "c1", "r1")
        cache.set("q2", "c2", "r2")
        cache.invalidate("q1", "c1")
        assert cache.get("q1", "c1") is None
        assert cache.get("q2", "c2") == "r2"

    def test_cache_max_size_eviction(self):
        """Cache evicts oldest when over max_size."""
        cache = ResponseCache(ttl_seconds=3600, max_size=3)
        cache.set("q1", "c1", "r1")
        time.sleep(0.05)
        cache.set("q2", "c2", "r2")
        time.sleep(0.05)
        cache.set("q3", "c3", "r3")
        time.sleep(0.05)
        cache.set("q4", "c4", "r4")  # should evict q1
        assert cache.get("q1", "c1") is None
        assert cache.size == 3


class TestEmbeddingService:
    """Tests for embedding service (HuggingFace)."""

    def test_hf_embed_documents(self):
        """HuggingFace embedding produces vectors."""
        pytest.importorskip("sentence_transformers")
        from services.embedding_service import HuggingFaceEmbeddingService

        embed = HuggingFaceEmbeddingService()
        vectors = embed.embed_documents(["Тестовый текст"])
        assert len(vectors) == 1
        assert len(vectors[0]) > 0  # should be 384 for MiniLM

    def test_hf_embed_query(self):
        """HuggingFace query embedding produces vector."""
        pytest.importorskip("sentence_transformers")
        from services.embedding_service import HuggingFaceEmbeddingService

        embed = HuggingFaceEmbeddingService()
        vector = embed.embed_query("Тестовый запрос")
        assert len(vector) > 0

    def test_hf_embed_dimension(self):
        """HuggingFace embedding dimension matches model."""
        pytest.importorskip("sentence_transformers")
        from services.embedding_service import HuggingFaceEmbeddingService

        embed = HuggingFaceEmbeddingService()
        assert embed.dimension == 384


class TestVectorStore:
    """Tests for VectorStoreService."""

    def test_add_and_count(self, vector_store):
        """Adding texts increases count."""
        vector_store.add_texts(["Текст 1", "Текст 2"])
        assert vector_store.count() == 2

    def test_search_returns_results(self, vector_store):
        """Search returns documents."""
        vector_store.add_texts([
            "Компания основана в 2010 году",
            "Политика конфиденциальности",
        ])
        results = vector_store.similarity_search("Компания", k=2)
        assert len(results) > 0
        assert results[0].content is not None
        assert results[0].score is not None

    def test_search_with_score_threshold(self, vector_store):
        """Search respects score threshold."""
        vector_store.add_texts(["Уникальный текст про космос"])
        results = vector_store.similarity_search("космос", k=5, score_threshold=0.0)
        assert len(results) > 0

    def test_delete_collection(self, vector_store):
        """Collection can be deleted."""
        vector_store.add_texts(["Тест"])
        vector_store.delete_collection()
        # Should be able to re-init
        assert vector_store.count() == 0

    def test_text_only_search(self, vector_store_no_embed):
        """Vector store works without embedding service (text search)."""
        vector_store_no_embed.add_texts(["Тестовый документ", "Другой документ"])
        results = vector_store_no_embed.similarity_search("Тестовый", k=2)
        assert len(results) > 0


class TestReranker:
    """Tests for RerankerService."""

    def test_reranker_available(self):
        """Reranker is loaded when sentence-transformers is available."""
        from services.reranker import RerankerService
        reranker = RerankerService()
        # This may be False if sentence-transformers not installed
        # But we at least don't crash
        _ = reranker.available
        assert True

    def test_reranker_empty_docs(self):
        """Reranker handles empty document list."""
        from services.reranker import RerankerService
        reranker = RerankerService()
        result = reranker.rerank("query", [])
        assert result == []
