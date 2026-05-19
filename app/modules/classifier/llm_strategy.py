"""LLM-based classifier strategy using Claude API.

Constitution V: Implements ClassifierProtocol — swappable via config.
"""

import json

import httpx

from app.core.logging import get_logger
from app.modules.classifier.keyword_urgency import UrgencyBooster
from app.modules.classifier.protocol import ClassifierProtocol
from app.modules.normalizer.protocol import NormalizedComplaint
from app.schemas.classification import ClassificationResult, SentimentEnum

logger = get_logger("classifier.llm")

SYSTEM_PROMPT = """You are a Pakistani government complaint classifier. Given a normalized complaint, classify it into:
1. department: One of [water_supply, electricity, roads, sanitation, police, health, education, revenue, gas, telecom]
2. sub_category: A specific sub-category within the department (e.g., outage, billing, quality, pothole, theft, etc.)
3. urgency_score: Float 0.0 to 1.0. Higher = more urgent. Consider: safety risk, number affected, duration of issue.
4. sentiment: One of [positive, negative, neutral]
5. confidence: Float 0.0 to 1.0. How confident are you in this classification.

Output MUST be valid JSON:
{
  "department": "<department_id>",
  "sub_category": "<sub_category>",
  "urgency_score": <float>,
  "sentiment": "<positive|negative|neutral>",
  "confidence": <float>
}

Examples:

Input: {"normalized_text": "Water has not been coming for 4 days in G-9", "extracted_intent": "water_supply_outage"}
Output: {"department": "water_supply", "sub_category": "outage", "urgency_score": 0.78, "sentiment": "negative", "confidence": 0.95}

Input: {"normalized_text": "Electricity bill is incorrect in F-7", "extracted_intent": "electricity_billing"}
Output: {"department": "electricity", "sub_category": "billing", "urgency_score": 0.4, "sentiment": "negative", "confidence": 0.92}

Input: {"normalized_text": "Large pothole on road, very dangerous", "extracted_intent": "road_pothole"}
Output: {"department": "roads", "sub_category": "pothole", "urgency_score": 0.72, "sentiment": "negative", "confidence": 0.90}

Input: {"normalized_text": "Child is sick, no space in hospital", "extracted_intent": "health_emergency"}
Output: {"department": "health", "sub_category": "emergency", "urgency_score": 0.95, "sentiment": "negative", "confidence": 0.93}

Input: {"normalized_text": "Gas leakage smell in entire street", "extracted_intent": "gas_leakage"}
Output: {"department": "gas", "sub_category": "leakage", "urgency_score": 0.92, "sentiment": "negative", "confidence": 0.88}

Return ONLY the JSON object."""

# Keyword-only fallback mapping for when LLM is unavailable
KEYWORD_DEPARTMENT_MAP: dict[str, str] = {
    "pani": "water_supply", "water": "water_supply", "paani": "water_supply",
    "bijli": "electricity", "electric": "electricity", "bill": "electricity", "meter": "electricity",
    "road": "roads", "sadak": "roads", "pothole": "roads", "signal": "roads",
    "kachra": "sanitation", "gandagi": "sanitation", "nala": "sanitation", "garbage": "sanitation", "sewage": "sanitation",
    "police": "police", "chori": "police", "theft": "police", "crime": "police",
    "hospital": "health", "doctor": "health", "dawai": "health", "sehat": "health",
    "school": "education", "teacher": "education", "college": "education",
    "zameen": "revenue", "tax": "revenue", "land": "revenue",
    "gas": "gas", "sui gas": "gas",
    "mobile": "telecom", "internet": "telecom", "signal": "telecom", "network": "telecom",
}


class LLMClassifier(ClassifierProtocol):
    """Few-shot LLM classifier using Claude API."""

    def __init__(self, http_client: httpx.AsyncClient, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.http_client = http_client
        self.api_key = api_key
        self.model = model
        self.urgency_booster = UrgencyBooster()

    async def classify(self, normalized: NormalizedComplaint) -> ClassificationResult:
        """Classify normalized complaint via LLM, then apply urgency boosting."""
        try:
            user_msg = json.dumps({
                "normalized_text": normalized.normalized_text,
                "extracted_intent": normalized.extracted_intent,
            })

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
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_msg}],
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"]

            parsed = json.loads(content)

            result = ClassificationResult(
                department=parsed.get("department", "water_supply"),
                sub_category=parsed.get("sub_category", "general"),
                urgency_score=float(parsed.get("urgency_score", 0.5)),
                sentiment=SentimentEnum(parsed.get("sentiment", "neutral")),
                confidence=float(parsed.get("confidence", 0.5)),
            )

            # Apply urgency keyword boosting (deterministic layer)
            result = self.urgency_booster.boost(result, normalized.original_text)
            return result

        except Exception as e:
            logger.warning("classifier_llm_failed", error=str(e))
            return self._keyword_fallback(normalized)

    def _keyword_fallback(self, normalized: NormalizedComplaint) -> ClassificationResult:
        """Keyword-only classification when LLM is unavailable."""
        text_lower = normalized.original_text.lower()
        department = "water_supply"  # default

        for keyword, dept in KEYWORD_DEPARTMENT_MAP.items():
            if keyword in text_lower:
                department = dept
                break

        result = ClassificationResult(
            department=department,
            sub_category="general",
            urgency_score=0.5,
            sentiment=SentimentEnum.NEGATIVE,
            confidence=0.3,
        )

        # Still apply urgency boosting even in fallback mode
        result = self.urgency_booster.boost(result, normalized.original_text)
        return result
