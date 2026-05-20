"""
NaqsKAR — Geo Extraction & Resolution Module
Extracts location entities from complaint text and resolves them
to coordinates using a custom Pakistan gazetteer + fuzzy matching.
"""
import json
import os
import logging
from rapidfuzz import process, fuzz
from app.models import GeoLocation

logger = logging.getLogger(__name__)

# Load the Pakistan gazetteer
GAZETTEER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gazetteer.json")

_gazetteer: list[dict] = []


def load_gazetteer():
    """Load Pakistan gazetteer from JSON file."""
    global _gazetteer
    try:
        with open(GAZETTEER_PATH, "r", encoding="utf-8") as f:
            _gazetteer = json.load(f)
        logger.info(f"Loaded {len(_gazetteer)} gazetteer entries")
    except FileNotFoundError:
        logger.warning("Gazetteer file not found, using empty gazetteer")
        _gazetteer = []


def resolve_location(raw_location: str | None) -> GeoLocation | None:
    """
    Resolve a raw location string to standardized name + coordinates.
    Uses fuzzy matching against Pakistan gazetteer.

    Args:
        raw_location: Location text extracted by the classifier (e.g., "G-9 islamabd")

    Returns:
        GeoLocation with resolved name and coordinates, or None if not found
    """
    if not raw_location or raw_location.strip().lower() in ["null", "none", ""]:
        return None

    if not _gazetteer:
        load_gazetteer()

    if not _gazetteer:
        return None

    raw_clean = raw_location.strip().lower()

    # Build lookup: all names and aliases from gazetteer
    name_to_entry = {}
    all_names = []
    for entry in _gazetteer:
        names = [entry["name"].lower()]
        names.extend([a.lower() for a in entry.get("aliases", [])])
        for name in names:
            name_to_entry[name] = entry
            all_names.append(name)

    # Fuzzy match
    match = process.extractOne(
        raw_clean,
        all_names,
        scorer=fuzz.WRatio,
        score_cutoff=65
    )

    if not match:
        logger.info(f"No geo match for: {raw_location}")
        return None

    matched_name, score, _ = match
    entry = name_to_entry[matched_name]

    confidence = min(score / 100.0, 1.0)

    logger.info(f"Geo resolved: '{raw_location}' → '{entry['name']}' (score={score})")

    return GeoLocation(
        raw_text=raw_location,
        resolved_name=entry["name"],
        latitude=entry["lat"],
        longitude=entry["lng"],
        confidence=confidence
    )
