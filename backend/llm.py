"""
LLM Gateway — unified interface to LLM providers.

Wraps concrete LLM services (OpenAI, YandexGPT, Mock) with:
  - Structured logging
  - Fallback / retry logic
  - Latency tracking
  - Unified generate / generate_stream interface

All production code routes LLM calls through this gateway.
"""

from __future__ import annotations

import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog

from models.schemas import SourceDocument
from services.llm_service import LLMService, create_llm_service

logger = structlog.get_logger()


class LLMGateway:
    """
    Gateway that wraps an LLMService with observability and resilience.

    Usage:
        gateway = LLMGateway.from_config(config)
        answer = gateway.generate(query, context, sources)
        async for token in gateway.generate_stream(query, context, sources):
            ...
    """

    def __init__(
        self,
        primary: LLMService,
        fallback: Optional[LLMService] = None,
    ):
        self._primary = primary
        self._fallback = fallback

    @classmethod
    def from_config(cls, config) -> "LLMGateway":
        """Factory: builds gateway from application Config."""
        effective = "mock" if config.mock_mode else config.llm_provider

        if effective == "mock":
            primary = create_llm_service(provider="mock")
        elif effective == "openai":
            primary = create_llm_service(
                provider="openai",
                api_key=config.openai_api_key,
                model=config.openai_model,
            )
        elif effective == "yandexgpt":
            primary = create_llm_service(
                provider="yandexgpt",
                api_key=config.yandexgpt_api_key,
                folder_id=config.yandexgpt_folder_id,
                model=config.yandexgpt_model,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {effective}")

        # Fallback to mock if nothing else works (safety net)
        fallback = None
        if effective != "mock":
            from services.llm_service import MockLLMService
            fallback = MockLLMService(delay=0.0)

        return cls(primary=primary, fallback=fallback)

    # ─── Synchronous generation ─────────────────────────────────────

    def generate(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate answer via primary provider with fallback.
        """
        start = time.time()
        try:
            answer = self._primary.generate(
                query=query,
                context=context,
                sources=sources,
                temperature=temperature,
            )
            latency = (time.time() - start) * 1000
            logger.info(
                "llm_generate_success",
                provider=self._primary.model_name,
                latency_ms=round(latency, 1),
                query_length=len(query),
                context_length=len(context),
            )
            return answer
        except Exception as exc:
            latency = (time.time() - start) * 1000
            logger.error(
                "llm_generate_failed",
                provider=self._primary.model_name,
                latency_ms=round(latency, 1),
                error=str(exc),
            )
            if self._fallback is not None:
                logger.warning(
                    "llm_fallback_activated",
                    fallback_provider=self._fallback.model_name,
                )
                return self._fallback.generate(query, context, sources, temperature)
            raise

    # ─── Streaming generation ───────────────────────────────────────

    async def generate_stream(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream tokens from primary provider with fallback.
        """
        start = time.time()
        try:
            token_count = 0
            async for token in self._primary.generate_stream(
                query=query,
                context=context,
                sources=sources,
                temperature=temperature,
            ):
                token_count += 1
                yield token
            latency = (time.time() - start) * 1000
            logger.info(
                "llm_stream_success",
                provider=self._primary.model_name,
                latency_ms=round(latency, 1),
                tokens=token_count,
            )
        except Exception as exc:
            latency = (time.time() - start) * 1000
            logger.error(
                "llm_stream_failed",
                provider=self._primary.model_name,
                latency_ms=round(latency, 1),
                error=str(exc),
            )
            if self._fallback is not None:
                logger.warning(
                    "llm_fallback_activated",
                    fallback_provider=self._fallback.model_name,
                )
                words = self._fallback.generate(query, context, sources, temperature).split()
                for word in words:
                    yield word + " "
            else:
                raise

    # ─── Properties ─────────────────────────────────────────────────

    @property
    def model_name(self) -> str:
        return self._primary.model_name

    def stats(self) -> Dict[str, Any]:
        return {
            "primary": self._primary.model_name,
            "fallback": self._fallback.model_name if self._fallback else None,
        }
