"""Keyword-based urgency boosting.

Deterministic post-processor that elevates urgency for safety-critical keywords.
Runs AFTER LLM classification to ensure urgency keywords are never missed.
"""

from app.core.logging import get_logger
from app.schemas.classification import ClassificationResult

logger = get_logger("classifier.urgency")

# Urgency keywords — presence of ANY triggers urgency >= 0.8
URGENCY_KEYWORDS: dict[str, list[str]] = {
    # Medical emergencies
    "medical": [
        "baccha", "bacha", "hospital", "ambulance", "zakhmi", "injured",
        "bimar", "sick", "emergency", "doctor", "dawa", "medicine",
        "pregnant", "hamal",
    ],
    # Violence / crime
    "violence": [
        "khoon", "blood", "maut", "death", "qatal", "murder",
        "chori", "theft", "daku", "dacoit", "kidnap", "harassment",
        "mara", "beaten",
    ],
    # Fire / disaster
    "fire": [
        "aag", "fire", "dhamaka", "blast", "explosion", "collapse",
        "slab", "girgaya", "fallen",
    ],
    # Infrastructure danger
    "danger": [
        "dangerous", "khatarnak", "bijli ka tar", "live wire",
        "gas leak", "gas leakage",
    ],
}

# Flatten for fast lookup
ALL_URGENCY_KEYWORDS: set[str] = set()
for keywords in URGENCY_KEYWORDS.values():
    ALL_URGENCY_KEYWORDS.update(keywords)


class UrgencyBooster:
    """Boosts urgency score when critical keywords are detected."""

    def boost(
        self, result: ClassificationResult, original_text: str
    ) -> ClassificationResult:
        """Check for urgency keywords and boost score if found.

        Args:
            result: Classification result from LLM.
            original_text: Original complaint text (for keyword matching).

        Returns:
            Updated ClassificationResult with boosted urgency if keywords found.
        """
        text_lower = original_text.lower()
        matched: list[str] = []

        for keyword in ALL_URGENCY_KEYWORDS:
            if keyword in text_lower:
                matched.append(keyword)

        if matched:
            new_urgency = max(result.urgency_score, 0.8)
            logger.info(
                "urgency_boosted",
                original_score=result.urgency_score,
                boosted_score=new_urgency,
                keywords=matched,
            )
            return result.model_copy(
                update={
                    "urgency_score": new_urgency,
                    "urgency_keywords_matched": matched,
                }
            )

        return result
