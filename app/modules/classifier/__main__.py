"""Classifier standalone demo.

Constitution II: Module-level __main__ for independent demonstration.
Run: python -m app.modules.classifier
"""

import asyncio
import os

import httpx

from app.modules.classifier.llm_strategy import LLMClassifier
from app.modules.normalizer.protocol import NormalizedComplaint


async def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set — demo will use keyword fallback")

    samples = [
        NormalizedComplaint(
            original_text="pani nahi araha 4 din se G-9 mein",
            normalized_text="Water has not been coming for 4 days in G-9",
            detected_language="roman_urdu",
            extracted_intent="water_supply_outage",
            extracted_entities={"duration": "4 days", "location": "G-9"},
            confidence=0.95,
        ),
        NormalizedComplaint(
            original_text="bijli ka bill galat hai F-7",
            normalized_text="Electricity bill is incorrect in F-7",
            detected_language="roman_urdu",
            extracted_intent="electricity_billing",
            extracted_entities={"location": "F-7"},
            confidence=0.90,
        ),
        NormalizedComplaint(
            original_text="baccha zakhmi hai hospital mein jagah nahi",
            normalized_text="Child is injured, no space in hospital",
            detected_language="roman_urdu",
            extracted_intent="health_emergency",
            extracted_entities={"severity_keywords": ["baccha", "zakhmi"]},
            confidence=0.93,
        ),
        NormalizedComplaint(
            original_text="road pe pothole dangerous hai",
            normalized_text="Dangerous pothole on road",
            detected_language="mixed",
            extracted_intent="road_pothole",
            extracted_entities={},
            confidence=0.88,
        ),
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        classifier = LLMClassifier(http_client=client, api_key=api_key)

        print("=" * 60)
        print("NaqsKAR — Multi-Label Classifier Demo")
        print("=" * 60)

        for sample in samples:
            print(f"\n📝 Input: {sample.original_text}")
            result = await classifier.classify(sample)
            print(f"   Department:  {result.department}")
            print(f"   Sub-cat:     {result.sub_category}")
            print(f"   Urgency:     {result.urgency_score:.2f}")
            print(f"   Sentiment:   {result.sentiment.value}")
            print(f"   Confidence:  {result.confidence:.2f}")
            if result.urgency_keywords_matched:
                print(f"   ⚠️  Keywords:  {result.urgency_keywords_matched}")

    print("\n✅ Classifier demo complete.")


if __name__ == "__main__":
    asyncio.run(main())
