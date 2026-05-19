"""Normalizer standalone demo.

Constitution II: Module-level __main__ for independent demonstration.
Run: python -m app.modules.normalizer
"""

import asyncio
import os

import httpx

from app.modules.normalizer.llm_strategy import LLMNormalizer


async def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set — demo will use fallback mode")

    samples = [
        ("pani nahi araha 4 din se G-9 mein", "roman_urdu"),
        ("بجلی کا بل غلط ہے اسلام آباد سیکٹر F-7", "urdu"),
        ("Pothole on Constitution Avenue near Marriott", "english"),
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        normalizer = LLMNormalizer(http_client=client, api_key=api_key)

        print("=" * 60)
        print("NaqsKAR — Multilingual Normalizer Demo")
        print("=" * 60)

        for text, lang in samples:
            print(f"\n📝 Input ({lang}): {text}")
            result = await normalizer.process(text, language_hint=lang)
            print(f"   Intent:     {result.extracted_intent}")
            print(f"   Normalized: {result.normalized_text}")
            print(f"   Language:   {result.detected_language}")
            print(f"   Entities:   {result.extracted_entities}")
            print(f"   Confidence: {result.confidence:.2f}")

    print("\n✅ Normalizer demo complete.")


if __name__ == "__main__":
    asyncio.run(main())
