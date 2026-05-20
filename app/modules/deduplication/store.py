"""In-memory cluster store with rolling window for semantic deduplication.

Constitution III: Thread-safe in-memory store with time-based expiration.
"""

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from app.core.logging import get_logger
from app.schemas.classification import ClassificationResult
from app.schemas.cluster import ClusterInfo
from app.schemas.location import LocationResult

logger = get_logger("dedup.store")


@dataclass
class ClusterEntry:
    """A single complaint stored for deduplication matching."""

    complaint_id: str
    text: str
    embedding: np.ndarray
    department: str
    urgency_score: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    cluster_id: Optional[str] = None


@dataclass
class Cluster:
    """A group of semantically similar, geographically proximate complaints."""

    cluster_id: str
    entries: list[ClusterEntry] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.entries)

    @property
    def weight(self) -> float:
        """Cluster weight = count × avg_urgency."""
        if not self.entries:
            return 0.0
        avg_urgency = sum(e.urgency_score for e in self.entries) / len(self.entries)
        return len(self.entries) * avg_urgency


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in meters."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class InMemoryClusterStore:
    """Rolling-window cluster store for deduplication.

    Clusters complaints by:
    - Cosine similarity >= threshold (default 0.7)
    - Haversine distance <= radius (default 500m)
    - Within time window (default 7 days)
    - Same department
    """

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        radius_meters: float = 500.0,
        window_days: int = 7,
    ) -> None:
        self.similarity_threshold = similarity_threshold
        self.radius_meters = radius_meters
        self.window_seconds = window_days * 86400
        self.entries: list[ClusterEntry] = []
        self.clusters: dict[str, Cluster] = {}

    def prune_expired(self) -> int:
        """Remove entries older than the time window. Returns count removed."""
        cutoff = time.time() - self.window_seconds
        before_count = len(self.entries)

        # Remove expired entries
        self.entries = [e for e in self.entries if e.timestamp >= cutoff]

        # Prune clusters with no remaining entries
        active_cluster_ids = {e.cluster_id for e in self.entries if e.cluster_id}
        expired_clusters = [
            cid for cid in self.clusters if cid not in active_cluster_ids
        ]
        for cid in expired_clusters:
            del self.clusters[cid]

        removed = before_count - len(self.entries)
        if removed > 0:
            logger.info("store_pruned", removed=removed, remaining=len(self.entries))
        return removed

    def find_cluster(
        self,
        embedding: np.ndarray,
        department: str,
        location: Optional[LocationResult] = None,
    ) -> Optional[tuple[str, float]]:
        """Find the best matching cluster for an embedding.

        Returns (cluster_id, similarity_score) or None.
        """
        self.prune_expired()

        best_cluster_id: Optional[str] = None
        best_similarity: float = 0.0

        for entry in self.entries:
            if entry.cluster_id is None:
                continue

            # Must be same department
            if entry.department != department:
                continue

            # Check cosine similarity
            similarity = _cosine_similarity(embedding, entry.embedding)
            if similarity < self.similarity_threshold:
                continue

            # Check geographic proximity (if both have locations)
            if location and location.latitude and location.longitude:
                if entry.latitude and entry.longitude:
                    dist = _haversine_meters(
                        location.latitude, location.longitude,
                        entry.latitude, entry.longitude,
                    )
                    if dist > self.radius_meters:
                        continue

            if similarity > best_similarity:
                best_similarity = similarity
                best_cluster_id = entry.cluster_id

        if best_cluster_id:
            return (best_cluster_id, best_similarity)
        return None

    def add(
        self,
        text: str,
        embedding: np.ndarray,
        classification: ClassificationResult,
        location: Optional[LocationResult] = None,
        cluster_id: Optional[str] = None,
    ) -> ClusterEntry:
        """Add a complaint to the store, optionally into an existing cluster."""
        # Create or join cluster
        if cluster_id is None:
            cluster_id = f"cluster_{uuid.uuid4().hex[:12]}"
            self.clusters[cluster_id] = Cluster(cluster_id=cluster_id)

        entry = ClusterEntry(
            complaint_id=f"complaint_{uuid.uuid4().hex[:8]}",
            text=text,
            embedding=embedding,
            department=classification.department,
            urgency_score=classification.urgency_score,
            latitude=location.latitude if location else None,
            longitude=location.longitude if location else None,
            cluster_id=cluster_id,
        )

        self.entries.append(entry)
        if cluster_id in self.clusters:
            self.clusters[cluster_id].entries.append(entry)

        return entry

    def get_cluster_info(self, cluster_id: str, similarity_score: float = 1.0) -> Optional[ClusterInfo]:
        """Build ClusterInfo response for a cluster."""
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return None

        return ClusterInfo(
            cluster_id=cluster_id,
            is_duplicate=cluster.size > 1,
            cluster_size=cluster.size,
            cluster_weight=round(cluster.weight, 2),
            similarity_score=round(similarity_score, 4),
        )
