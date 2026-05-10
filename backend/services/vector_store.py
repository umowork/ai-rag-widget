"""
Vector store service — wraps ChromaDB operations.
Handles adding, searching, deleting, and persisting documents.
Lazy imports for chromadb.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from models.schemas import DocumentMetadata, SourceDocument

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Wraps ChromaDB for persistent vector storage with metadata.
    """

    def __init__(
        self,
        persist_directory: str,
        embedding_service=None,
        collection_name: str = "rag_docs",
    ):
        """
        Args:
            persist_directory: Directory to store ChromaDB data.
            embedding_service: EmbeddingService instance.
            collection_name: Name of the Chroma collection.
        """
        self._persist_directory = persist_directory
        self._embedding_service = embedding_service
        self._collection_name = collection_name
        self._collection = None
        self._client = None

        os.makedirs(persist_directory, exist_ok=True)

    def _lazy_init(self):
        """Initialize ChromaDB client and collection on first use."""
        if self._collection is not None:
            return

        try:
            import chromadb  # lazy import
            from chromadb.config import Settings
        except ImportError as e:
            raise ImportError("chromadb required. Install: pip install chromadb") from e

        self._client = chromadb.PersistentClient(
            path=self._persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.debug(
            "ChromaDB initialized: dir=%s, collection=%s",
            self._persist_directory,
            self._collection_name,
        )

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """
        Add texts to the vector store.

        Args:
            texts: List of text chunks.
            metadatas: List of metadata dicts (same length as texts).
            ids: Optional list of IDs (auto-generated if None).

        Returns:
            Number of documents added.
        """
        self._lazy_init()
        if not texts:
            return 0

        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in texts]

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        # Generate embeddings
        if self._embedding_service:
            embeddings = self._embedding_service.embed_documents(texts)
        else:
            embeddings = None

        self._collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )
        logger.debug("Added %d documents to vector store", len(texts))
        return len(texts)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        score_threshold: Optional[float] = None,
    ) -> List[SourceDocument]:
        """
        Search for similar documents by query.

        Args:
            query: Search query text.
            k: Number of results.
            score_threshold: Minimum similarity score.

        Returns:
            List of SourceDocument with scores.
        """
        self._lazy_init()

        # Generate query embedding
        if self._embedding_service:
            query_embedding = self._embedding_service.embed_query(query)
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )
        else:
            results = self._collection.query(
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )

        documents = []
        if results["documents"] and results["documents"][0]:
            for i, doc_text in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results.get("distances") else 0.0
                score = 1.0 - distance  # cosine distance → similarity

                if score_threshold is not None and score < score_threshold:
                    continue

                doc_meta = DocumentMetadata(
                    source=meta.get("source", "unknown"),
                    page=meta.get("page"),
                    file_type=meta.get("file_type"),
                )

                documents.append(
                    SourceDocument(
                        content=doc_text,
                        metadata=doc_meta,
                        score=round(score, 4),
                    )
                )

        return documents

    def count(self) -> int:
        """Return number of documents in the collection."""
        self._lazy_init()
        return self._collection.count()

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self._lazy_init()
        try:
            self._client.delete_collection(self._collection_name)
            self._collection = None
            logger.info("Deleted collection: %s", self._collection_name)
        except Exception as e:
            logger.warning("Failed to delete collection: %s", e)

    def delete_by_ids(self, ids: List[str]) -> None:
        """Delete documents by their IDs."""
        self._lazy_init()
        if ids:
            self._collection.delete(ids=ids)
            logger.debug("Deleted %d documents from vector store", len(ids))

    def get_all_documents(self, limit: int = 100) -> List[SourceDocument]:
        """Retrieve all documents (for debugging/admin)."""
        self._lazy_init()
        results = self._collection.get(limit=limit, include=["documents", "metadatas"])
        docs = []
        if results["documents"]:
            for i, doc_text in enumerate(results["documents"]):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                doc_meta = DocumentMetadata(
                    source=meta.get("source", "unknown"),
                    page=meta.get("page"),
                    file_type=meta.get("file_type"),
                )
                docs.append(SourceDocument(content=doc_text, metadata=doc_meta))
        return docs
