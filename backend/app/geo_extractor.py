"""
NaqsKAR — Geo Extraction & Resolution Module
Extracts location entities from complaint text and resolves them
to coordinates using a custom Pakistan gazetteer + fuzzy matching.
"""
import json
import os
import logging
import re
from rapidfuzz import process, fuzz
from app.models import GeoLocation

logger = logging.getLogger(__name__)

# Load the Pakistan gazetteer
GAZETTEER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "gazetteer.json")

_gazetteer: list[dict] = []


DHA_PHASE_PATTERN = re.compile(
    r"(?<![a-z0-9])(?:dha|defen[cs]e)\s*(?:phase|ph)?\.?\s*[-:]?\s*\d+[a-z]?(?![a-z0-9])"
)


def _find_gazetteer_entry(name: str) -> dict | None:
    """Find a gazetteer entry by its canonical name."""
    name_clean = name.strip().lower()
    for entry in _gazetteer:
        if entry.get("name", "").strip().lower() == name_clean:
            return entry
    return None


def _extract_structured_location(text_lower: str) -> str | None:
    """
    Handle common Pakistani address shorthand that exact gazetteer aliases miss.
    Example: "Dha 6 mein..." means a DHA phase even without the word "phase".
    """
    if not DHA_PHASE_PATTERN.search(text_lower):
        return None

    if re.search(r"(?<![a-z0-9])(?:karachi|khi)(?![a-z0-9])", text_lower):
        entry = _find_gazetteer_entry("DHA, Karachi")
        if entry:
            return entry["name"]

    entry = _find_gazetteer_entry("DHA, Lahore")
    if entry:
        return entry["name"]

    return None


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


def extract_location_from_text(text: str) -> str | None:
    """
    Find the best gazetteer location mentioned directly in free text.
    This keeps geo working when the optional NER model is unavailable.
    """
    if not text or not text.strip():
        return None

    if not _gazetteer:
        load_gazetteer()

    if not _gazetteer:
        return None

    text_lower = text.lower()

    structured_match = _extract_structured_location(text_lower)
    if structured_match:
        return structured_match

    candidates: list[tuple[int, str]] = []

    for entry in _gazetteer:
        names = [entry["name"]]
        names.extend(entry.get("aliases", []))
        for name in names:
            name_clean = name.strip().lower()
            if not name_clean:
                continue

            pattern = rf"(?<![a-z0-9]){re.escape(name_clean)}(?![a-z0-9])"
            if re.search(pattern, text_lower):
                candidates.append((len(name_clean), entry["name"]))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


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

    direct_match = extract_location_from_text(raw_clean)
    if direct_match:
        raw_clean = direct_match.lower()

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
