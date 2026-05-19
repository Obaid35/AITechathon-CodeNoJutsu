# Research: NaqsKAR — AI Complaint Triage & Routing API

**Phase**: 0 — Outline & Research
**Date**: 2026-05-20

## R1: LLM Provider Strategy

**Decision**: Claude API (Anthropic) as primary, with Ollama (local) as fallback.

**Rationale**: Claude excels at few-shot classification and structured JSON output. The Anthropic SDK supports async natively (`anthropic.AsyncAnthropic`). For hackathon resilience, Ollama running a local model (e.g., Llama 3.1 8B or Gemma 2 9B) serves as the fallback when API latency spikes or quota is hit.

**Alternatives considered**:
- OpenAI GPT-4o: Strong but more expensive per-token; Anthropic SDK is more Pythonic.
- Google Gemini: Viable but team has more experience with Claude prompts.
- Local-only (Ollama): Too slow on CPU for hackathon demo reliability; good as fallback only.

**Implementation**: `httpx.AsyncClient` for Claude API calls. `ollama` Python package for local fallback. Strategy selected via `APP_LLM_PROVIDER` env var (`claude` | `ollama`).

---

## R2: Multilingual Normalization Approach

**Decision**: Few-shot LLM prompting for normalization (Day 1–2). Optionally fine-tune XLM-R if time permits on Day 3.

**Rationale**: Few-shot prompting with Claude handles Roman Urdu → structured intent extraction well out of the box. Fine-tuning XLM-R requires labeled data and training time that may not be available in a 3-day hackathon. The strategy pattern (Constitution Principle V) allows swapping later.

**Alternatives considered**:
- Fine-tuned mBERT: Better latency but requires training pipeline setup and labeled data.
- Rule-based transliteration: Fragile for code-mixed text; fails on creative spellings.
- Google Translate API + English NLP: Loses nuance in informal Roman Urdu.

**Prompt design**: System prompt defines the task + 5–8 few-shot examples covering Roman Urdu, Urdu script, English, and code-mixed. Output is constrained to JSON via Claude's response format.

---

## R3: Classification Model Strategy

**Decision**: Few-shot LLM classification with keyword-based urgency boosting as a post-processing layer.

**Rationale**: The LLM handles department + sub-category + sentiment in one call. Urgency keywords (baccha, hospital, khoon, aag, etc.) are deterministic — a keyword matcher runs after LLM classification and boosts urgency to ≥0.8 if triggered. This avoids relying on the LLM for safety-critical urgency detection.

**Department taxonomy** (initial 10):
1. `water_supply` — Water outages, quality, leaks
2. `electricity` — Power outages, billing, meters
3. `roads` — Potholes, traffic signals, road damage
4. `sanitation` — Sewage, garbage, drains
5. `police` — Crime, harassment, traffic violations
6. `health` — Hospital complaints, medical emergencies
7. `education` — School issues, teacher complaints
8. `revenue` — Land records, tax disputes
9. `gas` — Gas supply, leaks, billing
10. `telecom` — Network issues, billing disputes

---

## R4: Geo-Extraction & Gazetteer Design

**Decision**: Two-tier approach — deterministic gazetteer lookup first, LLM fallback for fuzzy/misspelled matches.

**Rationale**: A JSON gazetteer with ~500 entries (Islamabad sectors, major city neighborhoods, tehsils, landmarks) handles 80%+ of location mentions with zero latency. For misspelled or informal references (e.g., "G nain" instead of "G-9"), the LLM resolves the fuzzy match.

**Gazetteer structure**:
```json
{
  "entries": [
    {
      "name": "G-9",
      "aliases": ["g9", "g-9", "G nine", "G nain", "sector g9"],
      "city": "Islamabad",
      "lat": 33.7094,
      "lon": 73.0348
    }
  ]
}
```

**Alternatives considered**:
- OpenStreetMap Nominatim API: Good for formal addresses, poor for informal Pakistani location references.
- Google Maps Geocoding: Cost prohibitive at scale; overkill for sector codes.
- spaCy NER: Trained on Western location patterns; poor for Pakistani sector codes and Urdu landmarks.

---

## R5: Semantic Deduplication Architecture

**Decision**: sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`) for embeddings + scikit-learn DBSCAN for clustering, with an in-memory rolling-window store.

**Rationale**: `paraphrase-multilingual-MiniLM` supports Urdu and English out of the box. DBSCAN naturally handles variable cluster sizes and doesn't require pre-specifying K. The in-memory store avoids database complexity for the hackathon.

**Clustering parameters**:
- Time window: 7 days (configurable via `DEDUP_WINDOW_DAYS`)
- Geographic radius: 500m (configurable via `DEDUP_RADIUS_METERS`)
- Semantic similarity threshold: cosine distance ≤ 0.3 (configurable)

**Alternatives considered**:
- Qdrant vector DB: Production-grade but adds infra complexity for hackathon.
- pgvector: Requires PostgreSQL setup; overkill for MVP.
- FAISS: Good for large-scale but overhead not justified for demo volume.

**Performance note**: Embedding inference (~100ms per complaint on CPU) MUST run in `asyncio.to_thread()` per Constitution Principle III.

---

## R6: Dashboard Technology

**Decision**: Plain HTML/JS/CSS with Leaflet.js for the map. No build step.

**Rationale**: The hackathon timeline doesn't justify a Next.js setup for what is essentially one page with a map, filters, and a table. Leaflet is lightweight, CDN-served, and renders OpenStreetMap tiles. The dashboard fetches data from `/api/v1/analytics` via `fetch()`.

**Alternatives considered**:
- Next.js + Tailwind + Mapbox: Full-featured but 2+ hours of setup, build configuration, and hydration debugging for minimal gain.
- Streamlit: Quick to prototype but poor UX for a public-facing dashboard.
- Dash (Plotly): Python-based but heavy dependency and limited map customization.

---

## R7: Async Architecture Patterns

**Decision**: FastAPI lifespan context manager for initialization, `httpx.AsyncClient` as shared singleton, `asyncio.to_thread()` for CPU-bound ML, `asyncio.gather()` for parallel module execution within pipeline.

**Key patterns**:
```python
# Lifespan pattern (Constitution III)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models, init httpx client, warm caches
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    app.state.pipeline = await init_pipeline()
    yield
    await app.state.http_client.aclose()

# Thread offload for embeddings (Constitution III)
embedding = await asyncio.to_thread(model.encode, text)

# Parallel module execution where possible
normalized, geo = await asyncio.gather(
    normalizer.process(complaint),
    geo_extractor.extract(complaint.text)
)
```

---

## R8: Error Handling & Fallback Strategy

**Decision**: Three-tier fallback — primary LLM → fallback LLM → keyword-only degraded mode.

**Rationale**: Constitution Principle V (Swappable ML) and Principle VI (Production-Grade) both require graceful degradation. If Claude is down, try Ollama. If Ollama is also unavailable, fall back to a deterministic keyword-based classifier that maps known keywords to departments with lower confidence scores.

**Error response schema** (Constitution VI):
```json
{
  "error_code": "LLM_PROVIDER_UNAVAILABLE",
  "message": "Primary and fallback ML providers are unreachable",
  "details": {
    "primary": "claude: timeout after 30s",
    "fallback": "ollama: connection refused"
  }
}
```
