"""LLM + Gazetteer geo-extraction strategy.

Constitution V: Implements GeoExtractorProtocol — swappable via config.
Two-tier: deterministic gazetteer first, LLM fallback for fuzzy matches.
"""

import json
from typing import Optional

import httpx

from app.core.logging import get_logger
from app.modules.geo_extractor.gazetteer import Gazetteer
from app.modules.geo_extractor.protocol import GeoExtractorProtocol
from app.schemas.location import GeoSourceEnum, LocationResult

logger = get_logger("geo.llm")

GEO_SYSTEM_PROMPT = """You are a Pakistan geographic location resolver. Given complaint text, extract the location and resolve it.

Output MUST be valid JSON:
{
  "raw_location": "<location as mentioned in text>",
  "resolved_name": "<canonical name, e.g. 'G-9, Islamabad'>",
  "latitude": <float or null>,
  "longitude": <float or null>,
  "confidence": <0.0 to 1.0>,
  "city": "<city name or null>"
}

If no location is found in the text, return:
{"raw_location": "", "resolved_name": "", "latitude": null, "longitude": null, "confidence": 0.0, "city": null}

Focus on Pakistani locations: Islamabad sectors (F-6 to I-10), Lahore areas, Karachi neighborhoods, landmarks.
Handle misspellings: "G nain" = "G-9", "f7" = "F-7", "bluearea" = "Blue Area".

Return ONLY the JSON object."""


class LLMGeoExtractor(GeoExtractorProtocol):
    """Two-tier geo-extraction: gazetteer lookup first, LLM fallback."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        api_key: str,
        gazetteer: Optional[Gazetteer] = None,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        self.http_client = http_client
        self.api_key = api_key
        self.model = model
        self.gazetteer = gazetteer or Gazetteer()

    async def extract(
        self, text: str, location_hint: Optional[str] = None
    ) -> Optional[LocationResult]:
        """Extract location — gazetteer first, then LLM fallback."""
        search_text = location_hint or text

        # Tier 1: Deterministic gazetteer lookup
        entry = self.gazetteer.lookup(search_text)
        if entry:
            logger.info("geo_gazetteer_hit", location=entry.name)
            return LocationResult(
                raw_location=entry.name,
                resolved_name=f"{entry.name}, {entry.city}",
                latitude=entry.lat,
                longitude=entry.lon,
                confidence=0.95,
                source=GeoSourceEnum.GAZETTEER,
                city=entry.city,
            )

        # Also try the original text if location_hint was provided
        if location_hint and location_hint != text:
            entry = self.gazetteer.lookup(text)
            if entry:
                logger.info("geo_gazetteer_hit_text", location=entry.name)
                return LocationResult(
                    raw_location=entry.name,
                    resolved_name=f"{entry.name}, {entry.city}",
                    latitude=entry.lat,
                    longitude=entry.lon,
                    confidence=0.95,
                    source=GeoSourceEnum.GAZETTEER,
                    city=entry.city,
                )

        # Tier 2: LLM fallback for fuzzy / misspelled locations
        if not self.api_key:
            return None

        try:
            response = await self.http_client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 512,
                    "system": GEO_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": search_text}],
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"]
            parsed = json.loads(content)

            if not parsed.get("raw_location"):
                return None

            return LocationResult(
                raw_location=parsed.get("raw_location", ""),
                resolved_name=parsed.get("resolved_name", ""),
                latitude=parsed.get("latitude"),
                longitude=parsed.get("longitude"),
                confidence=float(parsed.get("confidence", 0.4)),
                source=GeoSourceEnum.LLM_FALLBACK,
                city=parsed.get("city"),
            )

        except Exception as e:
            logger.warning("geo_llm_failed", error=str(e))
            return None
