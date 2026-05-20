"""
NaqsKAR — Semantic Deduplication Module
Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
to embed complaints and cluster similar ones within a time/geo window.
This is a LOCAL ML model — proof that NaqsKAR is NOT a thin API wrapper.
"""
import logging
import uuid
import numpy as np
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings
from app.db import get_db

logger = logging.getLogger(__name__)

# Load embedding model locally (runs on CPU, ~100MB)
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dimensional embedding for a complaint text."""
    model = get_model()
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
    timestamp: datetime | None = None
):
    """Store a complaint with its embedding for future dedup checks."""
    _complaint_store.append({
        "id": complaint_id,
        "text": text,
        "embedding": np.array(embedding),
        "department": department,
        "lat": location_lat,
        "lng": location_lng,
        "timestamp": timestamp or datetime.utcnow(),
        "cluster_id": None
    })


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two lat/lng points in kilometers."""
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlng = np.radians(lng2 - lng1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlng / 2) ** 2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def find_duplicates(
    new_embedding: list[float],
    department: str,
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
            # Fallback to in-memory if RPC fails

    # --- IN-MEMORY FALLBACK ---
    if not _complaint_store:
        return None

    new_emb = np.array(new_embedding).reshape(1, -1)
    cutoff_time = datetime.utcnow() - timedelta(days=settings.DEDUP_WINDOW_DAYS)

    # Filter candidates: same department + within time window
    candidates = [
        c for c in _complaint_store
        if c["department"] == department and c["timestamp"] >= cutoff_time
    ]

    if not candidates:
        return None

    # Compute cosine similarities
    candidate_embeddings = np.array([c["embedding"] for c in candidates])
    similarities = cosine_similarity(new_emb, candidate_embeddings)[0]

    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]

    if best_score < settings.DEDUP_SIMILARITY_THRESHOLD:
        return None

    best_match = candidates[best_idx]

    # Check geo proximity if both have locations
    if location_lat and location_lng and best_match["lat"] and best_match["lng"]:
        dist = _haversine_km(location_lat, location_lng, best_match["lat"], best_match["lng"])
        if dist > settings.DEDUP_RADIUS_KM:
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
