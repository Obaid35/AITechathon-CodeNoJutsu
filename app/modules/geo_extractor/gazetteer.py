"""Pakistan gazetteer — deterministic location lookup.

Loads entries from app/data/pakistan_gazetteer.json and provides
substring + alias matching for fast geo-resolution.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger

logger = get_logger("geo.gazetteer")


@dataclass
class GazetteerEntry:
    """A single gazetteer entry."""

    name: str
    aliases: list[str]
    city: str
    lat: float
    lon: float


class Gazetteer:
    """Pakistan-specific location gazetteer with alias matching."""

    def __init__(self, data_path: Optional[str] = None) -> None:
        if data_path is None:
            data_path = str(
                Path(__file__).resolve().parent.parent.parent / "data" / "pakistan_gazetteer.json"
            )
        self.entries: list[GazetteerEntry] = []
        self._load(data_path)

    def _load(self, path: str) -> None:
        """Load gazetteer entries from JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("entries", []):
                self.entries.append(
                    GazetteerEntry(
                        name=entry["name"],
                        aliases=[a.lower() for a in entry.get("aliases", [])],
                        city=entry["city"],
                        lat=entry["lat"],
                        lon=entry["lon"],
                    )
                )
            logger.info("gazetteer_loaded", entries=len(self.entries))
        except Exception as e:
            logger.error("gazetteer_load_failed", error=str(e))

    def lookup(self, text: str) -> Optional[GazetteerEntry]:
        """Find the best matching gazetteer entry for the given text.

        Matching strategy:
        1. Exact name match (case-insensitive)
        2. Alias match (case-insensitive)
        3. Substring match on name/aliases

        Args:
            text: Text to search for location references.

        Returns:
            Best matching GazetteerEntry, or None if no match found.
        """
        text_lower = text.lower()

        # Pass 1: Exact name match
        for entry in self.entries:
            if entry.name.lower() in text_lower:
                return entry

        # Pass 2: Alias match
        for entry in self.entries:
            for alias in entry.aliases:
                if alias in text_lower:
                    return entry

        return None
