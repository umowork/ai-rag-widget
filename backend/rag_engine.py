"""
RAG Engine — the central coordinator.

Orchestrates document loading → chunking → embedding → vector search → LLM generation.
Replaces the old rag_engine.py with a clean, modular design.
No mocks in production code (use MOCK_MODE env flag for testing).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from models.schemas import DocumentMetadata, SourceDocument
from services.cache_service import ResponseCache
from services.document_service import DocumentProcessor
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService
from services.reranker import RerankerService
from services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Central RAG engine that coordinates all services.

    Typical flow:
        1. Document uploaded → DocumentProcessor chunks it
        2. Chunks → VectorStoreService (embeddings + store)
        3. Query → VectorStoreService.similarity_search → RerankerService
        4. Retrieved context + query → LLMService.generate → answer
    """

    def __init__(
        self,
        vector_store: VectorStoreService,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        document_processor: Optional[DocumentProcessor] = None,
        reranker: Optional[RerankerService] = None,
        cache: Optional[ResponseCache] = None,
        mock_mode: bool = False,
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.document_processor = document_processor or DocumentProcessor()
        self.reranker = reranker or RerankerService()
        self.cache = cache or ResponseCache()
        self.mock_mode = mock_mode

    # ─── Document Management ────────────────────────────────────────

    def add_text(
        self,
        text: str,
        source: str = "manual",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> int:
        """
        Add raw text to the vector store.

        Args:
            text: Text content.
            source: Source label.
            chunk_size: Max chunk size.
            chunk_overlap: Overlap between chunks.

        Returns:
            Number of chunks added.
        """
        processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunked = processor.chunk_text(
            text,
            metadata=DocumentMetadata(source=source, file_type="text"),
        )
        if len(chunked) == 0:
            return 0

        metadatas = [
            {k: v for k, v in {
                "source": cm.source,
                "page": cm.page,
                "file_type": cm.file_type or "text",
            }.items() if v is not None}
            for cm in chunked.chunk_metadata
        ]
        return self.vector_store.add_texts(chunked.chunks, metadatas=metadatas)

    def add_file(self, file_path: str, source: Optional[str] = None) -> int:
        """
        Load a file, chunk it, and add to vector store.

        Args:
            file_path: Path to document.
            source: Override source name (default: filename).

        Returns:
            Number of chunks added.
        """
        metadata = {}
        if source:
            metadata["source"] = source

        chunked = self.document_processor.load_and_chunk(file_path, metadata=metadata)

        if len(chunked) == 0:
            logger.warning("No content extracted from %s", file_path)
            return 0

        metadatas = [
            {k: v for k, v in {
                "source": cm.source,
                "page": cm.page,
                "file_type": cm.file_type,
            }.items() if v is not None}
            for cm in chunked.chunk_metadata
        ]
        return self.vector_store.add_texts(chunked.chunks, metadatas=metadatas)

    # ─── Search ─────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 4,
        rerank: bool = True,
    ) -> List[SourceDocument]:
        """
        Search the vector store for relevant documents.

        Args:
            query: Search query.
            top_k: Number of results.
            rerank: Whether to apply cross-encoder reranking.

        Returns:
            List of SourceDocument with scores.
        """
        documents = self.vector_store.similarity_search(query, k=top_k * 2 if rerank else top_k)

        if rerank and len(documents) > 1:
            documents = self.reranker.rerank(query, documents, top_k=top_k)
        else:
            documents = documents[:top_k]

        return documents

    # ─── Query → Answer ─────────────────────────────────────────────

    def query(
        self,
        query: str,
        top_k: int = 4,
        temperature: Optional[float] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline: search → generate answer.

        Args:
            query: User question.
            top_k: Number of documents to retrieve.
            temperature: LLM temperature override.
            use_cache: Whether to check cache first.

        Returns:
            Dict with 'answer', 'sources', 'model_used'.
        """
        # 1. Retrieve relevant documents
        sources = self.search(query, top_k=top_k)
        context = self._format_context(sources)

        # 2. Check cache
        if use_cache:
            cached = self.cache.get(query, context)
            if cached is not None:
                logger.debug("Cache hit for query: %s", query[:50])
                return {
                    "answer": cached,
                    "sources": sources,
                    "model_used": self.llm_service.model_name,
                    "cached": True,
                }

        # 3. Generate answer
        answer = self.llm_service.generate(
            query=query,
            context=context,
            sources=sources,
            temperature=temperature,
        )

        # 4. Cache the result
        if use_cache:
            self.cache.set(query, context, answer)

        return {
            "answer": answer,
            "sources": sources,
            "model_used": self.llm_service.model_name,
            "cached": False,
        }

    def query_stream(
        self,
        query: str,
        top_k: int = 4,
        temperature: Optional[float] = None,
    ):
        """
        Streaming RAG pipeline: search → stream generated tokens.

        Yields tokens from LLM, then sources.
        """
        # 1. Retrieve
        sources = self.search(query, top_k=top_k)
        context = self._format_context(sources)

        # 2. Stream answer
        yield from self.llm_service.generate_stream(
            query=query,
            context=context,
            sources=sources,
            temperature=temperature,
        )

        # 3. Yield metadata
        yield {"__sources__": [s.model_dump() for s in sources]}

    # ─── Helpers ────────────────────────────────────────────────────

    def _format_context(self, sources: List[SourceDocument]) -> str:
        """Format retrieved documents into a single context string."""
        parts = []
        for i, doc in enumerate(sources, start=1):
            source_name = doc.metadata.source
            parts.append(f"[Источник {i}: {source_name}]\n{doc.content}")
        return "\n\n---\n\n".join(parts)

    def stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        return {
            "vector_store_size": self.vector_store.count(),
            "embedding_model": self.embedding_service.model_name,
            "llm_model": self.llm_service.model_name,
            "mock_mode": self.mock_mode,
            "cache_size": self.cache.size,
            "reranker_available": self.reranker.available,
        }
