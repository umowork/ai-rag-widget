"""
Embedding service — converts text chunks to vectors.
Supports OpenAI text-embedding-ada-002 and HuggingFace sentence-transformers.
Lazy imports for heavy libraries (torch, sentence-transformers).
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingService(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts into vectors."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding vector dimension."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model name."""


class OpenAIEmbeddingService(EmbeddingService):
    """
    Uses OpenAI's text-embedding-ada-002 or text-embedding-3-small/large.
    Requires OPENAI_API_KEY env var.
    """

    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self._model_name = model
        self._dimension = 1536 if "ada-002" in model else 3072
        self._client = None
        self._api_key = api_key

    def _lazy_init(self):
        if self._client is not None:
            return
        try:
            from openai import OpenAI  # lazy import
            self._client = OpenAI(api_key=self._api_key)
        except ImportError as e:
            raise ImportError(
                "openai package is required. Install: pip install openai"
            ) from e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._lazy_init()
        if not texts:
            return []
        response = self._client.embeddings.create(
            input=texts, model=self._model_name
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        self._lazy_init()
        response = self._client.embeddings.create(
            input=[text], model=self._model_name
        )
        return response.data[0].embedding

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


class HuggingFaceEmbeddingService(EmbeddingService):
    """
    Uses sentence-transformers models.
    Lazy-imports torch and sentence-transformers.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._dim = 384  # default for MiniLM-L6-v2; updated on load

    def _lazy_init(self):
        if self._model is not None:
            return
        try:
            # Lazy imports for heavy libraries
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._dim = self._model.get_sentence_embedding_dimension()
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required. Install: pip install sentence-transformers"
            ) from e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._lazy_init()
        if not texts:
            return []
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        self._lazy_init()
        embedding = self._model.encode(text, show_progress_bar=False)
        return embedding.tolist()

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name


class MockEmbeddingService(EmbeddingService):
    """
    Deterministic mock embedding for testing / MOCK_MODE.
    Produces consistent vectors from a hash — no external dependencies.
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    def _text_to_vector(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode()).digest()
        raw = [b / 255.0 for b in digest]
        # Repeat or truncate to match dimension
        vec = (raw * ((self._dim // len(raw)) + 1))[:self._dim]
        # Normalize
        norm = sum(x * x for x in vec) ** 0.5
        return [x / norm for x in vec] if norm > 0 else vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._text_to_vector(text)

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return "mock-sha256"


def create_embedding_service(
    provider: str = "huggingface",
    api_key: str = "",
    model_name: str = "",
) -> EmbeddingService:
    """
    Factory: creates the appropriate embedding service.

    Args:
        provider: "openai" | "huggingface"
        api_key: Required for OpenAI.
        model_name: Override default model.

    Returns:
        Configured EmbeddingService instance.
    """
    provider = provider.lower().strip()
    if provider == "openai":
        model = model_name or "text-embedding-ada-002"
        logger.info("Creating OpenAI embedding service (model=%s)", model)
        return OpenAIEmbeddingService(api_key=api_key, model=model)
    elif provider == "huggingface":
        model = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        logger.info("Creating HuggingFace embedding service (model=%s)", model)
        return HuggingFaceEmbeddingService(model_name=model)
    elif provider == "mock":
        logger.info("Creating mock embedding service for testing")
        return MockEmbeddingService()
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. "
            "Use 'openai', 'huggingface', or 'mock'."
        )