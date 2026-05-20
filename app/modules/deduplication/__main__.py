"""Standalone deduplication demo.

Run: python -m app.modules.deduplication
"""

import asyncio
import sys

from app.modules.deduplication.embedding_strategy import EmbeddingDeduplicator
from app.modules.deduplication.store import InMemoryClusterStore


async def main():
    print("=== NaqsKAR Deduplication Demo ===\n")

    store = InMemoryClusterStore(
        similarity_threshold=0.7,
        radius_meters=500.0,
        window_days=7,
    )
    dedup = EmbeddingDeduplicator(store=store)

    # Sample complaints — 3 similar water complaints + 2 different ones
    from app.schemas.classification import ClassificationResult, SentimentEnum
    from app.schemas.location import LocationResult, GeoSourceEnum

    water_location = LocationResult(
        raw_location="G-9",
        resolved_name="G-9, Islamabad",
        latitude=33.7094,
        longitude=73.0348,
        confidence=0.95,
        source=GeoSourceEnum.GAZETTEER,
        city="Islamabad",
    )

    water_class = ClassificationResult(
        department="water_supply",
        sub_category="outage",
        urgency_score=0.78,
        sentiment=SentimentEnum.NEGATIVE,
        confidence=0.90,
    )

    samples = [
        ("pani nahi araha 4 din se G-9 mein", water_class, water_location),
        ("G-9 me paani ka masla hai, 4 din ho gaye", water_class, water_location),
        ("Water not coming in G-9 for 4 days now", water_class, water_location),
        (
            "Pothole on Constitution Avenue is dangerous",
            ClassificationResult(
                department="roads",
                sub_category="pothole",
                urgency_score=0.72,
                sentiment=SentimentEnum.NEGATIVE,
                confidence=0.88,
            ),
            None,
        ),
        (
            "bijli ka bill galat aaya hai F-7 mein",
            ClassificationResult(
                department="electricity",
                sub_category="billing",
                urgency_score=0.40,
                sentiment=SentimentEnum.NEGATIVE,
                confidence=0.85,
            ),
            None,
        ),
    ]

    for i, (text, classification, location) in enumerate(samples, 1):
        result = await dedup.deduplicate(text, classification, location)
        is_dup = result.is_duplicate if result else False
        cluster = result.cluster_id if result else "none"
        size = result.cluster_size if result else 0
        print(f"  [{i}] \"{text[:50]}...\"")
        print(f"      → cluster={cluster}, duplicate={is_dup}, size={size}")
        print()

    print(f"Total entries in store: {len(store.entries)}")
    print(f"Total clusters: {len(store.clusters)}")
    print()

    # Show cluster summary
    for cid, cluster in store.clusters.items():
        print(f"  Cluster {cid}: size={cluster.size}, weight={cluster.weight:.2f}")
        for entry in cluster.entries:
            print(f"    - {entry.text[:60]}...")


if __name__ == "__main__":
    asyncio.run(main())
