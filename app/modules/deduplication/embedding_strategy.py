"""Embedding-based deduplication strategy using sentence-transformers.

Constitution V: Implements DeduplicatorProtocol — swappable via config.
Constitution III: Uses asyncio.to_thread for CPU-bound embedding inference.
"""

import asyncio
from typing import Optional

import numpy as np

from app.core.logging import get_logger
from app.modules.deduplication.protocol import DeduplicatorProtocol
from app.modules.deduplication.store import InMemoryClusterStore
from app.schemas.classification import ClassificationResult
from app.schemas.cluster import ClusterInfo
from app.schemas.location import LocationResult

logger = get_logger("dedup.embedding")


class EmbeddingDeduplicator(DeduplicatorProtocol):
    """Semantic deduplication using multilingual sentence embeddings.

    Uses paraphrase-multilingual-MiniLM-L12-v2 for embedding text,
    then matches against the in-memory cluster store.
    """

    def __init__(
        self,
        store: InMemoryClusterStore,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ) -> None:
        self.store = store
        self.model_name = model_name
        self._model = None
        self._loading = False

    async def _ensure_model(self) -> None:
        """Lazy-load the embedding model on first use."""
        if self._model is not None:
            return

        if self._loading:
            # Another coroutine is loading — wait
            while self._loading:
                await asyncio.sleep(0.1)
            return

        self._loading = True
        try:
            logger.info("embedding_model_loading", model=self.model_name)
            # Load in thread to avoid blocking the event loop
            self._model = await asyncio.to_thread(self._load_model)
            logger.info("embedding_model_ready", model=self.model_name)
        finally:
            self._loading = False

    def _load_model(self):
        """Load sentence-transformers model (CPU-bound)."""
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(self.model_name)

    async def _encode(self, text: str) -> np.ndarray:
        """Encode text to embedding vector in a thread."""
        await self._ensure_model()
        embedding = await asyncio.to_thread(
            self._model.encode, text, normalize_embeddings=True
        )
        return np.array(embedding, dtype=np.float32)

    async def deduplicate(
        self,
        text: str,
        classification: ClassificationResult,
        location: Optional[LocationResult] = None,
    ) -> Optional[ClusterInfo]:
        """Check for duplicate complaints and cluster them.

        1. Encode the complaint text
        2. Search for matching cluster (similarity + proximity + time)
        3. If found → join cluster; if not → create new cluster
        4. Return ClusterInfo
        """
        try:
            embedding = await self._encode(text)

            # Search for existing cluster
            match = self.store.find_cluster(
                embedding=embedding,
                department=classification.department,
                location=location,
            )

            if match:
                cluster_id, similarity = match
                # Join existing cluster
                self.store.add(
                    text=text,
                    embedding=embedding,
                    classification=classification,
                    location=location,
                    cluster_id=cluster_id,
                )
                logger.info(
                    "dedup_matched",
                    cluster_id=cluster_id,
                    similarity=round(similarity, 4),
                )
                return self.store.get_cluster_info(cluster_id, similarity)

            else:
                # Create new cluster
                entry = self.store.add(
                    text=text,
                    embedding=embedding,
                    classification=classification,
                    location=location,
                )
                logger.info("dedup_new_cluster", cluster_id=entry.cluster_id)
                return self.store.get_cluster_info(entry.cluster_id)

        except Exception as e:
            logger.warning("dedup_failed", error=str(e))
            return None
