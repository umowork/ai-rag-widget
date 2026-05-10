"""
LLM service — generates answers from retrieved context.
Supports OpenAI, YandexGPT, and a mock for testing.
Lazy imports for heavy libraries (openai, httpx).
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from models.schemas import SourceDocument

logger = logging.getLogger(__name__)


class LLMService(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def generate(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ) -> str:
        """Generate answer from query + context."""

    @abstractmethod
    def generate_stream(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ):
        """Async generator yielding answer tokens."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""


class OpenAIService(LLMService):
    """
    Uses OpenAI chat completions (gpt-4o-mini, gpt-4o, gpt-3.5-turbo, etc.).
    Lazy-imports openai.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        system_prompt: Optional[str] = None,
    ):
        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt or (
            "Ты — AI-ассистент, который отвечает на вопросы на основе предоставленных "
            "документов компании. Отвечай точно по документам. Если в документах нет "
            "информации, честно скажи, что не знаешь. Используй русский язык."
        )
        self._client = None

    def _lazy_init(self):
        if self._client is not None:
            return
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
        except ImportError:
            raise ImportError("openai package required. Install: pip install openai") from None

    def _build_messages(self, query: str, context: str) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": (
                    f"Документы компании:\n---\n{context}\n---\n\n"
                    f"Вопрос: {query}\n\n"
                    f"Дай развернутый ответ на русском языке, основываясь только на документах."
                ),
            },
        ]

    def generate(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ) -> str:
        self._lazy_init()
        messages = self._build_messages(query, context)
        kwargs = {"model": self._model, "messages": messages}
        if temperature is not None:
            kwargs["temperature"] = temperature
        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ):
        self._lazy_init()
        messages = self._build_messages(query, context)
        kwargs = {
            "model": self._model,
            "messages": messages,
            "stream": True,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        stream = self._client.chat.completions.create(**kwargs)
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    @property
    def model_name(self) -> str:
        return self._model


class YandexGPTService(LLMService):
    """
    Uses YandexGPT API via HTTP.
    Requires YANDEXGPT_API_KEY and YANDEXGPT_FOLDER_ID env vars.
    Lazy-imports httpx.
    """

    API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def __init__(
        self,
        api_key: str,
        folder_id: str,
        model: str = "yandexgpt-lite",
        system_prompt: Optional[str] = None,
    ):
        self._api_key = api_key
        self._folder_id = folder_id
        self._model = model
        self._system_prompt = system_prompt or (
            "Ты — AI-ассистент, который отвечает на вопросы на основе предоставленных "
            "документов компании. Отвечай точно по документам. Используй русский язык."
        )

    def _build_payload(self, query: str, context: str, temperature: Optional[float] = None) -> dict:
        payload = {
            "modelUri": f"gpt://{self._folder_id}/{self._model}",
            "completionOptions": {
                "stream": False,
                "temperature": temperature if temperature is not None else 0.3,
                "maxTokens": "2000",
            },
            "messages": [
                {"role": "system", "text": self._system_prompt},
                {
                    "role": "user",
                    "text": (
                        f"Документы компании:\n---\n{context}\n---\n\n"
                        f"Вопрос: {query}\n\n"
                        f"Дай развернутый ответ на русском языке."
                    ),
                },
            ],
        }
        return payload

    def generate(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ) -> str:
        import httpx  # lazy import

        payload = self._build_payload(query, context, temperature)
        headers = {
            "Authorization": f"Api-Key {self._api_key}",
            "Content-Type": "application/json",
        }
        response = httpx.post(self.API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        try:
            return data["result"]["alternatives"][0]["message"]["text"]
        except (KeyError, IndexError):
            logger.error("Unexpected YandexGPT response: %s", data)
            return "Извините, не удалось получить ответ от YandexGPT."

    async def generate_stream(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ):
        # YandexGPT streaming via SSE — simplified sync wrapper for now
        text = self.generate(query, context, sources, temperature)
        words = text.split()
        for word in words:
            yield word + " "
            import asyncio
            await asyncio.sleep(0.03)

    @property
    def model_name(self) -> str:
        return self._model


class MockLLMService(LLMService):
    """
    Mock LLM for testing / MOCK_MODE=true.
    Returns formatted mock responses. NEVER used in production.
    """

    def __init__(self, delay: float = 0.0):
        self._delay = delay

    def generate(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ) -> str:
        if self._delay:
            time.sleep(self._delay)
        source_count = len(sources)
        return (
            f"📄 Ответ на вопрос: «{query}»\n\n"
            f"На основе {source_count} найденных документов:\n\n"
            f"{context[:500]}\n\n"
            f"---\n"
            f"⚙️ Режим MOCK — замените LLM_PROVIDER на 'openai' или 'yandexgpt' "
            f"для реальных ответов."
        )

    async def generate_stream(
        self,
        query: str,
        context: str,
        sources: List[SourceDocument],
        temperature: Optional[float] = None,
    ):
        text = self.generate(query, context, sources, temperature)
        words = text.split()
        for word in words:
            yield word + " "
            import asyncio
            await asyncio.sleep(0.03)

    @property
    def model_name(self) -> str:
        return "mock-llm"


def create_llm_service(
    provider: str = "openai",
    api_key: str = "",
    **kwargs,
) -> LLMService:
    """
    Factory: creates the appropriate LLM service.

    Args:
        provider: "openai" | "yandexgpt" | "mock"
        api_key: API key for the provider.
        **kwargs: Additional provider-specific args.

    Returns:
        Configured LLMService instance.
    """
    provider = provider.lower().strip()
    logger.info("Creating LLM service (provider=%s)", provider)

    if provider == "openai":
        return OpenAIService(api_key=api_key, **kwargs)
    elif provider == "yandexgpt":
        folder_id = kwargs.pop("folder_id", "")
        return YandexGPTService(api_key=api_key, folder_id=folder_id, **kwargs)
    elif provider == "mock":
        return MockLLMService(**kwargs)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Use 'openai', 'yandexgpt', or 'mock'."
        )
