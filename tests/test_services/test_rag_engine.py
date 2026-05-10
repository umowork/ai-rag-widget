"""
Tests for the RAGEngine — the central coordinator.
"""

from __future__ import annotations

import os

import pytest


@pytest.mark.asyncio
async def test_rag_engine_add_and_query(test_config):
    """RAGEngine can add text and query it."""
    from main import create_app
    from main import rag_engine

    # Create app to initialize rag_engine
    app = create_app(test_config)

    # Add text
    chunks = rag_engine.add_text("Компания основана в 2010 году в Москве.", source="about")
    assert chunks > 0

    # Query
    result = rag_engine.query("Когда основана компания?")
    assert "answer" in result
    assert len(result["answer"]) > 0
    assert "sources" in result
    assert len(result["sources"]) > 0


def test_rag_engine_add_and_search(test_config):
    """RAGEngine.search returns relevant documents."""
    from main import create_app, rag_engine

    app = create_app(test_config)

    rag_engine.add_text("Политика конфиденциальности обновлена в 2024 году.", source="privacy")
    results = rag_engine.search("Политика конфиденциальности", top_k=2)

    assert len(results) > 0
    assert results[0].content is not None
    assert "конфиденциальности" in results[0].content


def test_rag_engine_search_without_rerank(test_config):
    """RAGEngine.search works with rerank disabled."""
    from main import create_app, rag_engine

    cfg = test_config
    # Create a config with rerank disabled
    cfg_no_rerank = cfg  # reuse
    app = create_app(cfg_no_rerank)

    rag_engine.add_text("Контакты: email@company.com, телефон: +7 495 123-45-67", source="contacts")
    results = rag_engine.search("Email компании", top_k=2, rerank=False)

    assert len(results) > 0


def test_rag_engine_stats(test_config):
    """RAGEngine.stats() returns expected keys."""
    from main import create_app, rag_engine

    app = create_app(test_config)

    rag_engine.add_text("Test content.", source="test")
    stats = rag_engine.stats()

    assert "vector_store_size" in stats
    assert stats["vector_store_size"] > 0
    assert "embedding_model" in stats
    assert "llm_model" in stats
    assert "mock_mode" in stats
    assert stats["mock_mode"] is True
    assert "cache_size" in stats
