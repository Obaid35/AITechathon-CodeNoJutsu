"""Quick test: classify -> analytics flow."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import httpx, json

BASE = "http://localhost:8000"

# 1. Classify a complaint
print("=== Classifying complaint... ===")
r = httpx.post(f"{BASE}/api/v1/classify", json={"text": "pani nahi araha G-9 mein 3 din se"}, timeout=300)
print(f"Classify: {r.status_code} -> {r.json()['classification']['department']}")

# 2. Check analytics
print("\n=== Analytics after 1 complaint ===")
r2 = httpx.get(f"{BASE}/api/v1/analytics", timeout=10)
data = r2.json()
print(f"Total: {data['total_complaints']}")
print(f"By Dept: {data['by_department']}")
print(f"Clusters: {len(data['active_clusters'])}")
if data['active_clusters']:
    c = data['active_clusters'][0]
    print(f"  -> {c['cluster_id']}: {c['department']}, count={c['complaint_count']}, lat={c.get('latitude')}, lon={c.get('longitude')}")

print("\n=== Dashboard URL: http://localhost:8000/dashboard ===")
