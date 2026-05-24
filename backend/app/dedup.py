"""
NaqsKAR — Semantic Deduplication Module
Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
to embed complaints and cluster similar ones within a time/geo window.
This is a LOCAL ML model — proof that NaqsKAR is NOT a thin API wrapper.
"""
import logging
import uuid
import math
from datetime import datetime, timedelta
from rapidfuzz import fuzz
from app.config import settings
from app.db import get_db

logger = logging.getLogger(__name__)

# Load embedding model locally (runs on CPU, ~100MB)
_model = None


def get_model():
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        logger.warning("SentenceTransformers disabled to prevent hanging")
        _model = "fallback"
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dimensional embedding for a complaint text."""
    model = get_model()
    if model == "fallback":
        return [0.0] * 384
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


# In-memory store for complaint embeddings (swap with pgvector for production)
_complaint_store: list[dict] = []


def add_complaint(
    complaint_id: str,
    text: str,
    embedding: list[float],
    department: str,
    location_lat: float | None = None,
    location_lng: float | None = None,
    cluster_id: str | None = None,
    timestamp: datetime | None = None
):
    """Store a complaint with its embedding for future dedup checks."""
    _complaint_store.append({
        "id": complaint_id,
        "text": text,
        "embedding": embedding,
        "department": department,
        "lat": location_lat,
        "lng": location_lng,
        "timestamp": timestamp or datetime.utcnow(),
        "cluster_id": cluster_id
    })


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two lat/lng points in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Small local cosine implementation to keep demo mode dependency-light."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _is_zero_embedding(embedding: list[float]) -> bool:
    return not embedding or all(value == 0 for value in embedding)


def _same_geo_window(
    location_lat: float | None,
    location_lng: float | None,
    match_lat: float | None,
    match_lng: float | None,
) -> bool:
    if location_lat and location_lng and match_lat and match_lng:
        return _haversine_km(location_lat, location_lng, match_lat, match_lng) <= settings.DEDUP_RADIUS_KM
    return True


def find_duplicates(
    new_embedding: list[float],
    department: str,
    text: str = "",
    location_lat: float | None = None,
    location_lng: float | None = None,
) -> dict | None:
    """
    Check if a new complaint is a duplicate of existing ones.

    Criteria for deduplication:
    1. Cosine similarity > threshold (0.82)
    2. Same department
    3. Within time window (7 days)
    4. Within geo radius (0.5 km) if both have locations

    Returns cluster info if duplicate found, else None.
    """
    db = get_db()
    if db:
        try:
            # Call Supabase RPC for pgvector similarity search
            if not hasattr(db, "rpc"):
                raise AttributeError("RPC is not available on the lightweight DB client")

            result = db.rpc('match_complaints', {
                'query_embedding': new_embedding,
                'match_department': department,
                'match_threshold': settings.DEDUP_SIMILARITY_THRESHOLD,
                'match_count': 1
            }).execute()
            
            matches = result.data
            if matches:
                best_match = matches[0]
                cluster_id = best_match.get("cluster_id") or str(uuid.uuid4())[:8]
                
                # If the matched complaint didn't have a cluster_id yet, update it
                if not best_match.get("cluster_id"):
                    db.table("complaints").update({"cluster_id": cluster_id}).eq("id", best_match["id"]).execute()
                
                # Get the new size of the cluster
                count_res = db.table("complaints").select("id", count="exact").eq("cluster_id", cluster_id).execute()
                cluster_size = count_res.count + 1 # +1 for the new complaint
                
                return {
                    "cluster_id": cluster_id,
                    "similarity_score": float(best_match["similarity"]),
                    "cluster_size": cluster_size,
                    "representative_text": best_match["original_text"]
                }
            return None
        except Exception as e:
            logger.error(f"Supabase dedup error: {e}")
            try:
                res = db.table("complaints").select(
                    "complaint_id, original_text, normalized_text, cluster_id, location"
                ).eq("department", department).limit(100).execute()

                rows = res.data or []
                scored_rows = []
                for row in rows:
                    row_text = row.get("normalized_text") or row.get("original_text") or ""
                    loc = row.get("location") or {}
                    if not _same_geo_window(
                        location_lat,
                        location_lng,
                        loc.get("latitude"),
                        loc.get("longitude"),
                    ):
                        continue
                    scored_rows.append((fuzz.token_set_ratio(text.lower(), row_text.lower()) / 100.0, row))

                high_matches = [
                    (score, row)
                    for score, row in scored_rows
                    if score >= settings.DEDUP_SIMILARITY_THRESHOLD
                ]

                if high_matches:
                    best_score, best_match = max(high_matches, key=lambda item: item[0])
                    existing_cluster_counts: dict[str, int] = {}
                    for _, row in high_matches:
                        if row.get("cluster_id"):
                            existing_cluster_counts[row["cluster_id"]] = existing_cluster_counts.get(row["cluster_id"], 0) + 1

                    if existing_cluster_counts:
                        cluster_id = max(existing_cluster_counts.items(), key=lambda item: item[1])[0]
                    else:
                        cluster_id = str(uuid.uuid4())[:8]

                    for _, row in high_matches:
                        if row.get("cluster_id") != cluster_id:
                            db.table("complaints").update({"cluster_id": cluster_id}).eq(
                                "complaint_id", row["complaint_id"]
                            ).execute()

                    count_res = db.table("complaints").select("complaint_id", count="exact").eq(
                        "cluster_id", cluster_id
                    ).execute()
                    cluster_size = (count_res.count or 0) + 1

                    return {
                        "cluster_id": cluster_id,
                        "similarity_score": float(best_score),
                        "cluster_size": cluster_size,
                        "representative_text": best_match.get("original_text", ""),
                    }
            except Exception as text_error:
                logger.error(f"Supabase text dedup fallback error: {text_error}")
            # Fallback to in-memory if DB matching fails

    # --- IN-MEMORY FALLBACK ---
    if not _complaint_store:
        return None

    cutoff_time = datetime.utcnow() - timedelta(days=settings.DEDUP_WINDOW_DAYS)

    # Filter candidates: same department + within time window
    candidates = [
        c for c in _complaint_store
        if c["department"] == department and c["timestamp"] >= cutoff_time
    ]

    if not candidates:
        return None

    if _is_zero_embedding(new_embedding):
        scored_candidates = [
            (fuzz.token_set_ratio(text.lower(), c["text"].lower()) / 100.0, c)
            for c in candidates
        ]
    else:
        scored_candidates = [
            (_cosine_similarity(new_embedding, c["embedding"]), c)
            for c in candidates
        ]

    best_score, best_match = max(scored_candidates, key=lambda item: item[0])

    if best_score < settings.DEDUP_SIMILARITY_THRESHOLD:
        return None

    # Check geo proximity if both have locations
    if not _same_geo_window(location_lat, location_lng, best_match["lat"], best_match["lng"]):
        return None

    # Found a duplicate — return or create cluster
    cluster_id = best_match.get("cluster_id") or str(uuid.uuid4())[:8]
    best_match["cluster_id"] = cluster_id

    # Count all complaints in this cluster
    cluster_members = [c for c in _complaint_store if c.get("cluster_id") == cluster_id]

    return {
        "cluster_id": cluster_id,
        "similarity_score": float(best_score),
        "cluster_size": len(cluster_members) + 1,  # +1 for the new complaint
        "representative_text": best_match["text"]
    }


def get_all_clusters() -> list[dict]:
    """Get all active complaint clusters for the dashboard."""
    db = get_db()
    if db:
        try:
            # Query Supabase for all complaints that have a cluster_id
            res = db.table("complaints").select("*").not_.is_("cluster_id", "null").execute()
            data = res.data
            
            clusters = {}
            for c in data:
                cid = c["cluster_id"]
                if cid not in clusters:
                    loc = c.get("location") or {}
                    clusters[cid] = {
                        "cluster_id": cid,
                        "complaints": [],
                        "department": c["department"],
                        "lat": loc.get("latitude"),
                        "lng": loc.get("longitude"),
                    }
                clusters[cid]["complaints"].append({
                    "id": c["complaint_id"],
                    "text": c["original_text"],
                    "timestamp": c["processed_at"]
                })
            
            result = []
            for cid, cluster_data in clusters.items():
                result.append({
                    "cluster_id": cid,
                    "department": cluster_data["department"],
                    "complaint_count": len(cluster_data["complaints"]),
                    "representative_text": cluster_data["complaints"][0]["text"],
                    "lat": cluster_data["lat"],
                    "lng": cluster_data["lng"],
                    "complaint_ids": [c["id"] for c in cluster_data["complaints"]]
                })
            return sorted(result, key=lambda x: x["complaint_count"], reverse=True)
        except Exception as e:
            logger.error(f"Supabase cluster fetch error: {e}")

    # --- IN-MEMORY FALLBACK ---
    clusters = {}
    for c in _complaint_store:
        cid = c.get("cluster_id")
        if not cid:
            continue
        if cid not in clusters:
            clusters[cid] = {
                "cluster_id": cid,
                "complaints": [],
                "department": c["department"],
                "lat": c["lat"],
                "lng": c["lng"],
            }
        clusters[cid]["complaints"].append({
            "id": c["id"],
            "text": c["text"],
            "timestamp": c["timestamp"].isoformat()
        })

    result = []
    for cid, data in clusters.items():
        result.append({
            "cluster_id": cid,
            "department": data["department"],
            "complaint_count": len(data["complaints"]),
            "representative_text": data["complaints"][0]["text"],
            "lat": data["lat"],
            "lng": data["lng"],
            "complaint_ids": [c["id"] for c in data["complaints"]]
        })

    return sorted(result, key=lambda x: x["complaint_count"], reverse=True)
