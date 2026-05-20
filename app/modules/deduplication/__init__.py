"""Deduplication module factory and re-exports.

Constitution V: Runtime strategy selection via config.
"""

from typing import Optional

from app.core.config import Settings
from app.modules.deduplication.embedding_strategy import EmbeddingDeduplicator
from app.modules.deduplication.protocol import DeduplicatorProtocol
from app.modules.deduplication.store import InMemoryClusterStore


def create_deduplicator(
    settings: Settings,
) -> Optional[DeduplicatorProtocol]:
    """Factory: create deduplicator based on configured strategy.

    Returns None if dedup strategy is 'none'.
    """
    if settings.app_dedup_strategy.value == "embedding":
        store = InMemoryClusterStore(
            similarity_threshold=0.6,
            radius_meters=float(settings.dedup_radius_meters),
            window_days=settings.dedup_window_days,
        )
        return EmbeddingDeduplicator(store=store)
    elif settings.app_dedup_strategy.value == "none":
        return None
    else:
        return None
