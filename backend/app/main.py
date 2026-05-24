"""
NaqsKAR — Main FastAPI Application
AI-Powered Citizen Complaint Triage & Routing for Pakistan

Pipeline:
  1. Multilingual Normalizer (Groq LLM)
  2. Multi-Label Classifier (department, urgency, sentiment)
  3. Geo-Extractor (gazetteer + RapidFuzz)
  4. Semantic Deduplication (sentence-transformers + cosine similarity)
  5. Auto-Routing API (structured JSON output)
  6. Public Heatmap Dashboard (served via frontend)

Endpoints:
  POST /api/submit       — Submit a complaint → full pipeline
  POST /api/batch-seed   — Seed multiple complaints (demo helper)
  GET  /api/complaints   — List complaints with filters
  GET  /api/clusters     — Deduplicated complaint clusters
  GET  /api/stats        — Dashboard analytics
  GET  /api/departments  — Department routing directory
  GET  /api/pipeline     — Pipeline architecture info
  GET  /api/health       — Health check
"""
import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models import ComplaintSubmit, ComplaintResponse, ClassificationResult, GeoLocation
from app.classifier_v2 import classify_complaint
from app.geo_extractor import resolve_location, load_gazetteer
from app.dedup import generate_embedding, add_complaint, find_duplicates, get_all_clusters
from app.config import settings
from app.db import get_db

# ── Logging ────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("naqskar")

# ── In-memory complaint store ──────────────────────
complaints_db: list[dict] = []

# ── Department Routing Directory ───────────────────
DEPARTMENT_ROUTING = {
    "water_supply": {
        "authority": "WASA / CDA Water Wing",
        "sla_hours": 48,
        "escalation": "Deputy Commissioner",
        "contact": "UAN 111-500-786",
        "description": "Water supply outages, contamination, pipeline damage, tanker requests",
    },
    "electricity": {
        "authority": "IESCO / LESCO / K-Electric",
        "sla_hours": 24,
        "escalation": "NEPRA",
        "contact": "IESCO: 118, KE: 118",
        "description": "Load shedding, transformer failure, meter issues, billing disputes",
    },
    "gas_supply": {
        "authority": "SNGPL / SSGC",
        "sla_hours": 12,
        "escalation": "OGRA",
        "contact": "SNGPL: 1199, SSGC: 1199",
        "description": "Gas pressure issues, leaks, meter problems, new connections",
    },
    "roads_infrastructure": {
        "authority": "NHA / CDA / Municipal Corporation",
        "sla_hours": 72,
        "escalation": "Commissioner Office",
        "contact": "PHA: 1334",
        "description": "Potholes, broken roads, street lights, footpaths, bridges",
    },
    "sanitation_sewerage": {
        "authority": "Municipal Corporation / CDA Sanitation",
        "sla_hours": 24,
        "escalation": "Administrator Municipal",
        "contact": "MCB: 1334",
        "description": "Sewage overflow, drainage, garbage collection, waste management",
    },
    "health": {
        "authority": "District Health Authority",
        "sla_hours": 4,
        "escalation": "Secretary Health",
        "contact": "1166 (Health Helpline)",
        "description": "Hospital complaints, medicine shortage, ambulance, disease outbreak",
    },
    "education": {
        "authority": "District Education Authority",
        "sla_hours": 48,
        "escalation": "Secretary Education",
        "contact": "DEA Office",
        "description": "School complaints, teacher issues, infrastructure, admissions",
    },
    "police_security": {
        "authority": "District Police / SSP Office",
        "sla_hours": 2,
        "escalation": "IG Police",
        "contact": "15 (Emergency), 8787 (SMS)",
        "description": "Theft, harassment, missing persons, domestic violence, crime",
    },
    "fire_emergency": {
        "authority": "Rescue 1122 / Fire Brigade",
        "sla_hours": 0.5,
        "escalation": "NDMA",
        "contact": "1122 (Rescue), 16 (Fire)",
        "description": "Fire, explosion, building collapse, chemical hazard",
    },
    "public_transport": {
        "authority": "Punjab Mass Transit / Sindh Transport",
        "sla_hours": 48,
        "escalation": "Secretary Transport",
        "contact": "Varies by province",
        "description": "Bus/metro issues, route complaints, fare disputes",
    },
    "telecom": {
        "authority": "PTA / Telco Provider",
        "sla_hours": 72,
        "escalation": "PTA Consumer Wing",
        "contact": "0800-55-055 (PTA)",
        "description": "Internet, mobile signal, tower, broadband, PTCL",
    },
    "revenue_land": {
        "authority": "Board of Revenue / DC Office",
        "sla_hours": 120,
        "escalation": "Commissioner Revenue",
        "contact": "DC Office",
        "description": "Property disputes, land records, patwari issues, encroachment",
    },
    "environment": {
        "authority": "EPA / District Administration",
        "sla_hours": 72,
        "escalation": "Secretary Environment",
        "contact": "EPA Helpline",
        "description": "Pollution, smog, noise, deforestation, illegal dumping",
    },
    "general_complaint": {
        "authority": "District Administration / PCP",
        "sla_hours": 96,
        "escalation": "Commissioner Office",
        "contact": "Pakistan Citizen Portal",
        "description": "General grievances not fitting other categories",
    },
}


# ── Startup / Shutdown ─────────────────────────────
# ── Demo Seed Data ─────────────────────────────────
SEED_COMPLAINTS = [
    {"text": "Hamary ilaqe mein 3 din se pani nahi aa raha, tanker mafia ne qabza kar liya hai Lahore mein", "source": "web"},
    {"text": "Bijli ka transformer phat gaya hai aur poora mohalla andhera hai Islamabad G-9 mein", "source": "whatsapp"},
    {"text": "Gas ka pressure itna kam hai k chulha hi nahi jalta, khana kaise pakayen Karachi mein", "source": "web"},
    {"text": "Sarak par itna bada gaddha hai k 2 gaarian kharab ho chuki hain Rawalpindi mein", "source": "ivr"},
    {"text": "Nale ka paani ghar mein aa raha hai bohut gandagi hai Faisalabad mein", "source": "web"},
    {"text": "Hospital mein doctor nahi hai aur emergency band hai bachon ko kahan le jayen Multan mein", "source": "whatsapp"},
    {"text": "School ki building girne wali hai bachon ki jaan ko khatra hai Peshawar mein", "source": "web"},
    {"text": "Chori ho gayi hai police thana mein FIR nahi likhte koi sunwai nahi Quetta mein", "source": "ivr"},
    {"text": "Godam mein aag lag gayi hai fire brigade nahi aa raha please help Hyderabad mein", "source": "whatsapp"},
    {"text": "Metro bus ki timing theek nahi roz late aati hai Lahore mein", "source": "web"},
    {"text": "Internet aur mobile signal bilkul nahi aata pichle hafte se tower band hai Abbottabad mein", "source": "web"},
    {"text": "Patwari riswat maang raha hai zameen ki registry nahi kar raha Sialkot mein", "source": "ivr"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load resources on startup."""
    logger.info("🚀 NaqsKAR starting up...")
    load_gazetteer()
    logger.info("📍 Gazetteer loaded")

    logger.info("🧠 Loading embedding model (first time may take ~30s)...")
    try:
        generate_embedding("test warmup")
        logger.info("✅ Embedding model ready")
    except Exception as e:
        logger.warning(f"⚠️ Embedding model load deferred: {e}")

    # Auto-seed if no complaints exist
    db = get_db()
    has_data = False
    if db:
        try:
            res = db.table("complaints").select("complaint_id").limit(1).execute()
            has_data = bool(res.data)
        except Exception:
            pass
    if settings.AUTO_SEED_DEMO_DATA and not has_data and not complaints_db:
        logger.info("📦 No complaints found — auto-seeding demo data...")
        for seed in SEED_COMPLAINTS:
            try:
                c = ComplaintSubmit(text=seed["text"], source=seed["source"])
                await submit_complaint(c)
                logger.info(f"  ✅ Seeded: {seed['text'][:50]}...")
            except Exception as e:
                logger.warning(f"  ⚠️ Seed failed: {e}")
        logger.info(f"📦 Seeded {len(SEED_COMPLAINTS)} demo complaints")

    logger.info("✅ NaqsKAR ready to accept complaints")
    yield
    logger.info("👋 NaqsKAR shutting down")


# ── FastAPI App ────────────────────────────────────
app = FastAPI(
    title="NaqsKAR API",
    description=(
        "AI-Powered Citizen Complaint Triage & Routing for Pakistan.\n\n"
        "**Pipeline:** Multilingual Normalizer → Multi-Label Classifier → "
        "Geo-Extractor → Semantic Deduplicator → Auto-Router\n\n"
        "**Supported languages:** Roman Urdu, Urdu script (اردو), English, Code-mixed\n\n"
        "Built by **Code no Jutsu** for FYS 2026 AI Techathon"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ───────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "service": "NaqsKAR",
        "version": "1.0.0",
        "team": "Code no Jutsu",
        "groq_configured": bool(settings.GROQ_API_KEY),
        "complaints_count": len(complaints_db),
        "modules": {
            "normalizer": "active",
            "classifier": "active",
            "geo_extractor": "active",
            "deduplicator": "active",
            "router": "active",
        },
    }


# ── Pipeline Info ──────────────────────────────────
@app.get("/api/pipeline", tags=["System"])
async def pipeline_info():
    """Returns the technical architecture of the NaqsKAR pipeline."""
    return {
        "name": "NaqsKAR AI Pipeline",
        "version": "1.0.0",
        "modules": [
            {
                "id": 1,
                "name": "Multilingual Normalizer",
                "tech": "Groq Llama 3.1 8B",
                "description": "Converts Roman Urdu, Urdu, English, and code-mixed text into normalized structured intent",
                "type": "LLM",
            },
            {
                "id": 2,
                "name": "Department Classifier",
                "tech": "Fine-tuned XLM-RoBERTa (local, 82% accuracy)",
                "description": "Classifies complaint into 13 government departments using locally trained model",
                "type": "Local ML",
            },
            {
                "id": 3,
                "name": "Urgency Classifier",
                "tech": "Fine-tuned XLM-RoBERTa (local)",
                "description": "Predicts urgency level: critical, high, medium, low",
                "type": "Local ML",
            },
            {
                "id": 4,
                "name": "Sentiment Classifier",
                "tech": "Fine-tuned XLM-RoBERTa (local)",
                "description": "Detects citizen sentiment: angry, frustrated, neutral, polite",
                "type": "Local ML",
            },
            {
                "id": 5,
                "name": "Location Extractor (NER)",
                "tech": "Davlan/xlm-roberta-base-ner-hrl (local, pre-trained)",
                "description": "Extracts location entities from raw complaint text",
                "type": "Local ML",
            },
            {
                "id": 6,
                "name": "Keyword Extractor",
                "tech": "KeyBERT + paraphrase-multilingual-MiniLM-L12-v2 (local)",
                "description": "Extracts top keywords using MMR for diversity",
                "type": "Local ML",
            },
            {
                "id": 7,
                "name": "Geo-Resolver",
                "tech": "RapidFuzz + Custom Pakistan Gazetteer (46+ locations)",
                "description": "Fuzzy-matches extracted locations to lat/lng coordinates",
                "type": "NLP",
            },
            {
                "id": 8,
                "name": "Semantic Deduplicator",
                "tech": "sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) + cosine similarity",
                "description": "Embeds complaints locally, clusters duplicates within 7-day window and 500m radius",
                "type": "Local ML",
            },
            {
                "id": 9,
                "name": "Auto-Router",
                "tech": "Custom routing engine with SLA-aware department directory",
                "description": "Maps classified complaints to the responsible authority with SLA and escalation path",
                "type": "Rules Engine",
            },
        ],
        "models_used": [
            {"name": "XLM-RoBERTa (fine-tuned)", "provider": "Local", "purpose": "Department, Urgency, Sentiment classification"},
            {"name": "XLM-RoBERTa NER", "provider": "Local (HuggingFace)", "purpose": "Location entity extraction"},
            {"name": "KeyBERT", "provider": "Local", "purpose": "Keyword extraction"},
            {"name": "paraphrase-multilingual-MiniLM-L12-v2", "provider": "Local (HuggingFace)", "purpose": "Semantic embeddings for deduplication"},
            {"name": "Llama 3.1 8B", "provider": "Groq (Cloud)", "purpose": "Translation only (Roman Urdu → English)"},
        ],
        "languages_supported": ["Roman Urdu", "Urdu (اردو)", "English", "Code-mixed (Roman Urdu + English)"],
    }


# ── Submit Complaint ───────────────────────────────
@app.post("/api/submit", response_model=ComplaintResponse, tags=["Complaints"])
async def submit_complaint(complaint: ComplaintSubmit):
    """
    Process a raw citizen complaint through the full NaqsKAR pipeline:
    1. Normalize & classify (Groq LLM)
    2. Extract & resolve geo location (gazetteer + fuzzy matching)
    3. Generate embedding (local sentence-transformers)
    4. Check for semantic duplicates
    5. Route to responsible authority
    6. Return structured JSON with all results
    """
    complaint_id = str(uuid.uuid4())[:12]
    logger.info(f"📥 New complaint [{complaint_id}]: {complaint.text[:80]}...")

    # Step 1: Classify using Groq Llama 3.1
    classification_raw = await classify_complaint(complaint.text)

    classification = ClassificationResult(
        department=classification_raw["department"],
        sub_category=classification_raw.get("sub_category", "general"),
        urgency=classification_raw["urgency"],
        urgency_score=classification_raw["urgency_score"],
        sentiment=classification_raw["sentiment"],
        keywords=classification_raw.get("keywords", []),
    )

    # Step 2: Extract and resolve location
    raw_location = classification_raw.get("extracted_location")
    location = resolve_location(raw_location)

    # Step 3: Generate embedding (local sentence-transformers model)
    normalized_text = classification_raw.get("normalized_text", complaint.text)
    embedding = generate_embedding(normalized_text)

    # Step 4: Check for duplicates
    cluster_info = find_duplicates(
        new_embedding=embedding,
        department=classification.department.value,
        text=normalized_text,
        location_lat=location.latitude if location else None,
        location_lng=location.longitude if location else None,
    )

    cluster_id = None
    cluster_size = None
    if cluster_info:
        cluster_id = cluster_info["cluster_id"]
        cluster_size = cluster_info["cluster_size"]
        logger.info(f"🔗 Duplicate detected → cluster {cluster_id} (size: {cluster_size})")

    # Step 5: Store complaint with embedding
    add_complaint(
        complaint_id=complaint_id,
        text=normalized_text,
        embedding=embedding,
        department=classification.department.value,
        location_lat=location.latitude if location else None,
        location_lng=location.longitude if location else None,
        cluster_id=cluster_id,
    )

    # Step 6: Get routing info
    routing = DEPARTMENT_ROUTING.get(classification.department.value, DEPARTMENT_ROUTING["general_complaint"])

    record = {
        "id": complaint_id,
        "original_text": complaint.text,
        "normalized_text": normalized_text,
        "department": classification.department.value,
        "sub_category": classification.sub_category,
        "urgency": classification.urgency.value,
        "urgency_score": classification.urgency_score,
        "sentiment": classification.sentiment.value,
        "keywords": classification.keywords,
        "location": location.model_dump() if location else None,
        "cluster_id": cluster_id,
        "cluster_size": cluster_size,
        "source": complaint.source,
        "routing": routing,
        "suggested_response_urdu": classification_raw.get(
            "suggested_response_urdu",
            "آپ کی شکایت موصول ہو گئی ہے۔ متعلقہ محکمے کو بھیج دی گئی ہے۔"
        ),
        "processed_at": datetime.utcnow().isoformat(),
    }
    
    # Try Supabase first
    db = get_db()
    if db:
        try:
            db.table("complaints").insert({
                "complaint_id": complaint_id,
                "original_text": complaint.text,
                "normalized_text": normalized_text,
                "department": classification.department.value,
                "sub_category": classification.sub_category,
                "urgency": classification.urgency.value,
                "urgency_score": classification.urgency_score,
                "sentiment": classification.sentiment.value,
                "keywords": classification.keywords,
                "location": location.model_dump() if location else None,
                "embedding": embedding,
                "cluster_id": cluster_id,
                "source": complaint.source,
                "suggested_response_urdu": record["suggested_response_urdu"]
            }).execute()
        except Exception as e:
            logger.error(f"Failed to insert into Supabase: {e}")
            complaints_db.append(record) # Fallback
    else:
        complaints_db.append(record)

    logger.info(f"✅ [{complaint_id}]: {classification.department.value} | {classification.urgency.value} | score={classification.urgency_score} → {routing['authority']}")

    return ComplaintResponse(
        id=complaint_id,
        original_text=complaint.text,
        normalized_text=normalized_text,
        classification=classification,
        location=location,
        cluster_id=cluster_id,
        cluster_size=cluster_size,
        suggested_response_urdu=record["suggested_response_urdu"],
        processed_at=record["processed_at"],
    )


# ── Batch Seed (Demo Helper) ──────────────────────
class BatchSeedRequest(BaseModel):
    complaints: list[str]
    source: str = "demo"


@app.post("/api/batch-seed", tags=["Demo"])
async def batch_seed(req: BatchSeedRequest):
    """Seed multiple complaints at once for demo purposes."""
    results = []
    for text in req.complaints:
        try:
            c = ComplaintSubmit(text=text, source=req.source)
            result = await submit_complaint(c)
            results.append({"id": result.id, "department": result.classification.department, "urgency": result.classification.urgency, "status": "ok"})
        except Exception as e:
            results.append({"text": text[:50], "status": "error", "error": str(e)})
    return {"seeded": len(results), "results": results}


# ── List Complaints ────────────────────────────────
@app.get("/api/complaints", tags=["Complaints"])
async def list_complaints(
    department: Optional[str] = Query(None, description="Filter by department"),
    urgency: Optional[str] = Query(None, description="Filter by urgency level"),
    source: Optional[str] = Query(None, description="Filter by intake source"),
    limit: int = Query(50, ge=1, le=200),
):
    """List all complaints with optional filters."""
    db = get_db()
    if db:
        try:
            query = db.table("complaints").select("*").order("urgency_score", desc=True).limit(limit)
            if department:
                query = query.eq("department", department)
            if urgency:
                query = query.eq("urgency", urgency)
            if source:
                query = query.eq("source", source)
            
            res = query.execute()
            results = res.data
            
            # Map Supabase complaint_id back to id for the frontend
            for r in results:
                r["id"] = r.pop("complaint_id", r.get("id"))
                r["routing"] = DEPARTMENT_ROUTING.get(r["department"], DEPARTMENT_ROUTING["general_complaint"])
                
            return {"total": len(results), "complaints": results}
        except Exception as e:
            logger.error(f"Supabase list complaints error: {e}")

    # Fallback
    results = complaints_db.copy()

    if department:
        results = [c for c in results if c["department"] == department]
    if urgency:
        results = [c for c in results if c["urgency"] == urgency]
    if source:
        results = [c for c in results if c["source"] == source]

    results.sort(key=lambda x: x["urgency_score"], reverse=True)

    # Serialize datetime
    serialized = []
    for r in results[:limit]:
        sr = {**r}
        if isinstance(sr.get("processed_at"), datetime):
            sr["processed_at"] = sr["processed_at"].isoformat()
        serialized.append(sr)

    return {"total": len(results), "complaints": serialized}


# ── Get Clusters ───────────────────────────────────
@app.get("/api/clusters", tags=["Deduplication"])
async def get_clusters():
    """Get all deduplicated complaint clusters with weight scores."""
    clusters = get_all_clusters()

    # Add weight calculation: count × average_urgency
    db = get_db()
    for cluster in clusters:
        cids = cluster.get("complaint_ids", [])
        
        if db:
            try:
                res = db.table("complaints").select("urgency_score, department").in_("complaint_id", cids).execute()
                matching = res.data
            except Exception:
                matching = [c for c in complaints_db if c["id"] in cids]
        else:
            matching = [c for c in complaints_db if c["id"] in cids]

        if matching:
            avg_urgency = sum(c["urgency_score"] for c in matching) / len(matching)
            cluster["weight"] = round(cluster["complaint_count"] * avg_urgency, 2)
            cluster["avg_urgency"] = round(avg_urgency, 2)
            cluster["department"] = matching[0]["department"]
        else:
            cluster["weight"] = 0
            cluster["avg_urgency"] = 0

    clusters.sort(key=lambda x: x.get("weight", 0), reverse=True)

    return {"total_clusters": len(clusters), "clusters": clusters}


# ── Department Routing Directory ───────────────────
@app.get("/api/departments", tags=["Routing"])
async def list_departments():
    """Returns the full department routing directory with SLAs and contacts."""
    return {"departments": DEPARTMENT_ROUTING}


# ── Dashboard Stats ────────────────────────────────
@app.get("/api/stats", tags=["Analytics"])
async def get_stats():
    """Comprehensive analytics for the dashboard."""
    db = get_db()
    if db:
        try:
            res = db.table("complaints").select("*").execute()
            all_complaints = res.data
        except Exception:
            all_complaints = complaints_db
    else:
        all_complaints = complaints_db

    if not all_complaints:
        return {
            "total_complaints": 0,
            "by_department": {},
            "by_urgency": {},
            "by_source": {},
            "avg_urgency_score": 0,
            "top_locations": [],
            "clusters_active": 0,
            "recent_critical": [],
        }

    by_dept = {}
    by_urgency = {}
    by_source = {}

    for c in all_complaints:
        d = c["department"]
        by_dept[d] = by_dept.get(d, 0) + 1

        u = c["urgency"]
        by_urgency[u] = by_urgency.get(u, 0) + 1

        s = c.get("source", "web")
        by_source[s] = by_source.get(s, 0) + 1

    avg_score = sum(c["urgency_score"] for c in all_complaints) / len(all_complaints)

    loc_counts = {}
    for c in all_complaints:
        loc = c.get("location")
        if loc and isinstance(loc, dict) and "resolved_name" in loc:
            name = loc["resolved_name"]
            loc_counts[name] = loc_counts.get(name, 0) + 1
    top_locs = sorted(
        [{"name": k, "count": v} for k, v in loc_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]

    clusters = get_all_clusters()

    # Recent critical/high complaints
    critical = [c for c in all_complaints if c["urgency"] in ("critical", "high")]
    critical.sort(key=lambda x: x["urgency_score"], reverse=True)
    recent_critical = []
    for c in critical[:5]:
        loc = c.get("location")
        rc = {
            "id": c.get("complaint_id", c.get("id")),
            "text": c["original_text"][:100],
            "department": c["department"],
            "urgency": c["urgency"],
            "urgency_score": c["urgency_score"],
            "location": loc["resolved_name"] if loc and isinstance(loc, dict) else None,
        }
        recent_critical.append(rc)

    return {
        "total_complaints": len(all_complaints),
        "by_department": by_dept,
        "by_urgency": by_urgency,
        "by_source": by_source,
        "avg_urgency_score": round(avg_score, 2),
        "top_locations": top_locs,
        "clusters_active": len(clusters),
        "recent_critical": recent_critical,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
