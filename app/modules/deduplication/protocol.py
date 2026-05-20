"""Deduplication protocol — abstract interface for complaint deduplication.

Constitution V: Protocol-based module boundaries for swappable strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.classification import ClassificationResult
from app.schemas.cluster import ClusterInfo
from app.schemas.location import LocationResult


class DeduplicatorProtocol(ABC):
    """Abstract interface for complaint deduplication and clustering."""

    @abstractmethod
    async def deduplicate(
        self,
        text: str,
        classification: ClassificationResult,
        location: Optional[LocationResult] = None,
    ) -> Optional[ClusterInfo]:
        """Check if a complaint is a duplicate and return cluster info.

        Args:
            text: Original complaint text.
            classification: Classification result for the complaint.
            location: Resolved location (if available).

        Returns:
            ClusterInfo if a matching cluster was found or created, None otherwise.
        """
        ...
