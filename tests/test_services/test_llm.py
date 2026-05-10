"""
Tests for LLM service classes.
"""

from __future__ import annotations

import pytest

from models.schemas import DocumentMetadata, SourceDocument
from services.llm_service import MockLLMService, create_llm_service


class TestMockLLMService:
    """Tests for MockLLMService."""

    def test_mock_generates_answer(self, sample_source_docs):
        """Mock LLM returns a non-empty answer."""
        llm = MockLLMService()
        answer = llm.generate(
            query="Что компания делает?",
            context="Компания занимается ИИ.",
            sources=sample_source_docs,
        )
        assert answer is not None
        assert len(answer) > 0
        assert "MOCK" in answer or "mock" in answer.lower() or "Что компания делает?" in answer

    def test_mock_mentions_query(self, sample_source_docs):
        """Mock answer includes the original query."""
        llm = MockLLMService()
        answer = llm.generate(
            query="Какой телефон?",
            context="Телефон: +7 495 123-45-67",
            sources=sample_source_docs,
        )
        assert "Какой телефон?" in answer

    def test_mock_stream(self, sample_source_docs):
        """Mock stream yields tokens."""
        llm = MockLLMService()
        tokens = []
        import asyncio

        async def collect():
            async for token in llm.generate_stream(
                query="Вопрос?",
                context="Контекст.",
                sources=sample_source_docs,
            ):
                tokens.append(token)
            return tokens

        asyncio.run(collect())
        assert len(tokens) > 0
        # Should be words with spaces
        assert all(t.endswith(" ") for t in tokens)

    def test_mock_model_name(self):
        """Mock LLM service has correct model name."""
        llm = MockLLMService()
        assert llm.model_name == "mock-llm"


class TestCreateLLMService:
    """Tests for the LLM service factory."""

    def test_create_mock(self):
        """Factory creates MockLLMService when provider='mock'."""
        svc = create_llm_service(provider="mock")
        assert isinstance(svc, MockLLMService)
        assert svc.model_name == "mock-llm"

    def test_create_unknown_provider(self):
        """Factory raises ValueError for unknown provider."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_service(provider="unknown_provider")
