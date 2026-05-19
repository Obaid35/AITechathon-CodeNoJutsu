"""Geo-Extractor standalone demo.

Constitution II: Module-level __main__ for independent demonstration.
Run: python -m app.modules.geo_extractor
"""

import asyncio
import os

import httpx

from app.modules.geo_extractor.llm_strategy import LLMGeoExtractor


async def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set — only gazetteer matching available")

    samples = [
        ("pani nahi araha 4 din se G-9 mein", None),
        ("bijli nahi hai I-8 sector mein", None),
        ("pothole near Marriott Hotel Islamabad", None),
        ("kachra hai Johar Town Lahore", None),
        ("no location mentioned in this complaint", None),
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        geo = LLMGeoExtractor(http_client=client, api_key=api_key)

        print("=" * 60)
        print("NaqsKAR — Geo-Extractor Demo")
        print("=" * 60)

        for text, hint in samples:
            print(f"\n📍 Input: {text}")
            result = await geo.extract(text, location_hint=hint)
            if result:
                print(f"   Location:   {result.resolved_name}")
                print(f"   Lat/Lon:    {result.latitude}, {result.longitude}")
                print(f"   Source:     {result.source.value}")
                print(f"   Confidence: {result.confidence:.2f}")
            else:
                print("   ❌ No location found")

    print("\n✅ Geo-Extractor demo complete.")


if __name__ == "__main__":
    asyncio.run(main())
