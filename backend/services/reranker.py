"""
Reranker service — re-ranks retrieved documents for better relevance.
Uses a lightweight cross-encoder model. Lazy imports for torch.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from models.schemas import SourceDocument

logger = logging.getLogger(__name__)


class RerankerService:
    """
    Cross-encoder reranker that scores query-document pairs.
    Lazy-loads torch and sentence-transformers cross-encoder.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self._model_name = model_name
        self._model = None

    def _lazy_init(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self._model_name)
            logger.info("Loaded reranker model: %s", self._model_name)
        except ImportError:
            logger.warning(
                "sentence-transformers not installed; reranker disabled. "
                "Install: pip install sentence-transformers"
            )
            self._model = None

    @property
    def available(self) -> bool:
        """Check if reranker model is loaded."""
        if self._model is None:
            self._lazy_init()
        return self._model is not None

    def rerank(
        self,
        query: str,
        documents: List[SourceDocument],
        top_k: Optional[int] = None,
    ) -> List[SourceDocument]:
        """
        Re-rank documents by query-document relevance.

        Args:
            query: The user query.
            documents: List of SourceDocument to re-rank.
            top_k: Number of top results to return (default: all).

        Returns:
            Re-ranked list of SourceDocument objects.
        """
        if not documents:
            return []

        if not self.available:
            logger.debug("Reranker not available; returning original order")
            return documents

        pairs = [(query, doc.content) for doc in documents]
        scores = self._model.predict(pairs)

        # Attach scores and sort
        scored = list(zip(documents, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        top_k = top_k or len(documents)
        result = []
        for doc, score in scored[:top_k]:
            doc.score = round(float(score), 4)
            result.append(doc)

        top = result[0].score if result else 0
        logger.debug("Reranked %d docs, top score: %.4f", len(documents), top)
        return result
