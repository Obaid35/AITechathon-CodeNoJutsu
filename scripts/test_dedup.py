"""Quick dedup test — 3 similar water complaints should cluster together."""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import httpx
import json

BASE = "http://localhost:8000/api/v1/classify"
TIMEOUT = 300  # First run downloads embedding model (~500MB)

complaints = [
    {"text": "pani nahi araha 4 din se G-9 mein"},
    {"text": "G-9 me paani ka masla hai, 4 din ho gaye"},
    {"text": "Water supply issue in G-9 for past 4 days"},
]

print("=== DEDUP TEST: 3 similar water complaints ===\n")

results = []
for i, c in enumerate(complaints, 1):
    print(f"  Sending complaint {i}...")
    r = httpx.post(BASE, json=c, timeout=TIMEOUT)
    data = r.json()
    results.append(data)

    cluster = data.get("cluster")
    cid = cluster.get("cluster_id", "none") if cluster else "none"
    dup = cluster.get("is_duplicate", False) if cluster else False
    size = cluster.get("cluster_size", 0) if cluster else 0
    weight = cluster.get("cluster_weight", 0) if cluster else 0
    dept = data["classification"]["department"]
    print(f"  [{i}] dept={dept}, cluster={cid}, duplicate={dup}, size={size}, weight={weight}")
    print()

print("=== DONE ===")
