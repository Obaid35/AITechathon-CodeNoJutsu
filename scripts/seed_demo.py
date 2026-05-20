"""Seed demo data — POSTs sample complaints to the API for demo/testing.

Usage: python scripts/seed_demo.py [--delay 2] [--base-url http://localhost:8000]
"""

import json
import sys
import time
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import httpx


def main():
    parser = argparse.ArgumentParser(description="Seed NaqsKAR with demo complaints")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between requests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--timeout", type=float, default=300, help="Request timeout seconds")
    args = parser.parse_args()

    # Load sample complaints
    data_path = Path(__file__).resolve().parent.parent / "app" / "data" / "sample_complaints.json"
    with open(data_path, "r", encoding="utf-8") as f:
        complaints = json.load(f)

    print(f"🇵🇰 NaqsKAR Demo Seeder")
    print(f"   Base URL: {args.base_url}")
    print(f"   Complaints: {len(complaints)}")
    print(f"   Delay: {args.delay}s between requests")
    print(f"{'='*60}\n")

    results = {"success": 0, "error": 0, "departments": {}}

    for i, complaint in enumerate(complaints, 1):
        text = complaint["text"]
        lang = complaint.get("language", "auto")

        print(f"  [{i:2d}/{len(complaints)}] {text[:60]}...")
        sys.stdout.flush()

        try:
            start = time.time()
            r = httpx.post(
                f"{args.base_url}/api/v1/classify",
                json={"text": text, "language": lang},
                timeout=args.timeout,
            )
            elapsed = time.time() - start

            if r.status_code == 200:
                data = r.json()
                dept = data["classification"]["department"]
                urgency = data["classification"]["urgency_score"]
                loc = data.get("location", {})
                loc_name = loc.get("resolved_name", "unknown") if loc else "unknown"
                cluster = data.get("cluster", {})
                is_dup = cluster.get("is_duplicate", False) if cluster else False

                results["success"] += 1
                results["departments"][dept] = results["departments"].get(dept, 0) + 1

                dup_flag = " 🔁 DUP" if is_dup else ""
                print(f"         ✅ {dept} | urgency={urgency:.2f} | 📍 {loc_name} | {elapsed:.1f}s{dup_flag}")
            else:
                results["error"] += 1
                print(f"         ❌ HTTP {r.status_code}: {r.text[:100]}")

        except Exception as e:
            results["error"] += 1
            print(f"         ❌ Error: {e}")

        if i < len(complaints):
            time.sleep(args.delay)

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 RESULTS")
    print(f"   ✅ Success: {results['success']}")
    print(f"   ❌ Failed:  {results['error']}")
    print(f"\n   By Department:")
    for dept, count in sorted(results["departments"].items(), key=lambda x: -x[1]):
        print(f"     {dept}: {count}")

    print(f"\n🌐 Dashboard: {args.base_url}/dashboard")
    print(f"📡 Analytics: {args.base_url}/api/v1/analytics")


if __name__ == "__main__":
    main()
