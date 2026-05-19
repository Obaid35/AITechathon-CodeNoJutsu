"""Geo-Extractor protocol — abstract interface for location extraction.

Constitution V: Strategy pattern via ABC.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.location import LocationResult


class GeoExtractorProtocol(ABC):
    """Abstract base class for geographic extraction strategies."""

    @abstractmethod
    async def extract(
        self, text: str, location_hint: Optional[str] = None
    ) -> Optional[LocationResult]:
        """Extract and resolve geographic location from complaint text.

        Args:
            text: Raw or normalized complaint text.
            location_hint: Optional pre-extracted location from form field.

        Returns:
            LocationResult if a location was found, None otherwise.
        """
        ...
