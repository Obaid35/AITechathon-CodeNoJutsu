"""LLM-based normalizer strategy using Claude API.

Constitution V: Implements NormalizerProtocol — swappable via config.
Constitution III: Uses httpx.AsyncClient for async LLM calls.
"""

import json

import httpx

from app.core.logging import get_logger
from app.modules.normalizer.protocol import NormalizedComplaint, NormalizerProtocol

logger = get_logger("normalizer.llm")

SYSTEM_PROMPT = """You are a Pakistani complaint normalization system. You receive citizen complaints in Roman Urdu, Urdu script, English, or code-mixed text and extract structured information.

Your output MUST be valid JSON with these exact fields:
{
  "normalized_text": "<complaint translated/normalized to clear English>",
  "detected_language": "<roman_urdu|urdu|english|mixed>",
  "extracted_intent": "<intent_keyword like water_supply_outage, electricity_billing, road_pothole, etc.>",
  "extracted_entities": {
    "duration": "<if mentioned, e.g. '4 days'>",
    "location": "<if mentioned, e.g. 'G-9 Islamabad'>",
    "severity_keywords": ["<any urgency words found>"],
    "affected_service": "<specific service mentioned>"
  },
  "confidence": <0.0 to 1.0>
}

Examples:

Input: "pani nahi araha 4 din se G-9 mein"
Output: {"normalized_text": "Water has not been coming for 4 days in G-9", "detected_language": "roman_urdu", "extracted_intent": "water_supply_outage", "extracted_entities": {"duration": "4 days", "location": "G-9", "severity_keywords": [], "affected_service": "water supply"}, "confidence": 0.95}

Input: "بجلی کا بل غلط ہے اسلام آباد سیکٹر F-7"
Output: {"normalized_text": "Electricity bill is incorrect in Islamabad Sector F-7", "detected_language": "urdu", "extracted_intent": "electricity_billing", "extracted_entities": {"duration": null, "location": "F-7 Islamabad", "severity_keywords": [], "affected_service": "electricity billing"}, "confidence": 0.92}

Input: "road pe bohot badi hole h bilkul dangerous hai F-10 markaz"
Output: {"normalized_text": "There is a very large pothole on the road, it is very dangerous in F-10 Markaz", "detected_language": "mixed", "extracted_intent": "road_pothole", "extracted_entities": {"duration": null, "location": "F-10 Markaz", "severity_keywords": ["dangerous"], "affected_service": "roads"}, "confidence": 0.90}

Input: "Pothole on Constitution Avenue near Marriott"
Output: {"normalized_text": "Pothole on Constitution Avenue near Marriott Hotel", "detected_language": "english", "extracted_intent": "road_pothole", "extracted_entities": {"duration": null, "location": "Constitution Avenue, Marriott", "severity_keywords": [], "affected_service": "roads"}, "confidence": 0.95}

Input: "baccha bimar hai hospital mein jagah nahi mil rahi Jinnah Hospital"
Output: {"normalized_text": "Child is sick, cannot find space in Jinnah Hospital", "detected_language": "roman_urdu", "extracted_intent": "health_emergency", "extracted_entities": {"duration": null, "location": "Jinnah Hospital", "severity_keywords": ["baccha", "bimar"], "affected_service": "health"}, "confidence": 0.93}

Return ONLY the JSON object, no markdown formatting or extra text."""


class LLMNormalizer(NormalizerProtocol):
    """Few-shot LLM normalizer using Claude API."""

    def __init__(self, http_client: httpx.AsyncClient, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.http_client = http_client
        self.api_key = api_key
        self.model = model

    async def process(self, text: str, language_hint: str | None = None) -> NormalizedComplaint:
        """Normalize complaint text via Claude API few-shot prompting."""
        user_message = text
        if language_hint:
            user_message = f"[Language hint: {language_hint}] {text}"

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
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"]

            # Parse JSON from LLM response
            parsed = json.loads(content)

            return NormalizedComplaint(
                original_text=text,
                normalized_text=parsed.get("normalized_text", text),
                detected_language=parsed.get("detected_language", language_hint or "mixed"),
                extracted_intent=parsed.get("extracted_intent", "unknown"),
                extracted_entities=parsed.get("extracted_entities", {}),
                confidence=float(parsed.get("confidence", 0.5)),
            )

        except Exception as e:
            logger.warning("normalizer_llm_failed", error=str(e))
            # Fallback: return raw text with low confidence
            return NormalizedComplaint(
                original_text=text,
                normalized_text=text,
                detected_language=language_hint or "mixed",
                extracted_intent="unknown",
                extracted_entities={},
                confidence=0.2,
            )
