# Tasks: NaqsKAR — AI Complaint Triage & Routing API

**Input**: Design documents from `specs/001-complaint-triage-api/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested — test tasks are omitted. Add via follow-up if needed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency configuration

- [x] T001 Create project directory structure per plan.md (`app/`, `app/api/v1/`, `app/core/`, `app/schemas/`, `app/modules/normalizer/`, `app/modules/classifier/`, `app/modules/geo_extractor/`, `app/modules/deduplication/`, `app/orchestrator/`, `app/data/`, `dashboard/`, `tests/unit/`, `tests/integration/`, `tests/contract/`)
- [x] T002 Create `requirements.txt` with pinned dependencies: fastapi==0.100.0, uvicorn==0.23.0, pydantic==2.0.0, pydantic-settings, httpx, anthropic, sentence-transformers, scikit-learn, python-dotenv, numpy, structlog
- [x] T003 [P] Create `.env.example` with all config variables from quickstart.md (`ANTHROPIC_API_KEY`, `APP_LLM_PROVIDER`, `APP_NORMALIZER_STRATEGY`, `APP_CLASSIFIER_STRATEGY`, `APP_GEO_STRATEGY`, `APP_DEDUP_STRATEGY`, `HOST`, `PORT`, `DEBUG`, `DEDUP_WINDOW_DAYS`, `DEDUP_RADIUS_METERS`)
- [x] T004 [P] Create `app/core/config.py` — Pydantic Settings class loading all env vars with defaults, strategy enum types (`llm`|`keyword`|`none`), LLM provider enum (`claude`|`ollama`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create `app/core/errors.py` — `ErrorResponse` Pydantic model with `error_code`, `message`, `details` fields; `NaqsKARException` base class; `ValidationError` and `ProviderUnavailableError` subclasses
- [x] T006 [P] Create `app/core/logging.py` — Structured JSON logger using structlog, middleware that generates `request_id` (UUID4) per request and injects it into log context, log fields: `request_id`, `module`, `duration_ms`, `status`
- [x] T007 Create `app/schemas/complaint.py` — `ClassifyRequest` model (text: str min=3 max=5000, language: Optional[LanguageEnum], user_id: Optional[str] max=128, timestamp: Optional[datetime], location_hint: Optional[str]) and `BatchClassifyRequest` model (complaints: list[ClassifyRequest] min=1 max=100). Include `model_config` with `json_schema_extra` examples per Constitution IV
- [x] T008 [P] Create `app/schemas/classification.py` — `ClassificationResult` model (department: str, sub_category: str, urgency_score: float 0-1, sentiment: SentimentEnum, confidence: float, urgency_keywords_matched: list[str]) and `ClassifyResponse` model (schema_version: str="1.0", request_id: str, classification, location, cluster, suggested_response_urdu, processing_time_ms, _warnings: Optional[list])
- [x] T009 [P] Create `app/schemas/location.py` — `LocationResult` model (raw_location, resolved_name, latitude: Optional[float], longitude: Optional[float], confidence: float, source: SourceEnum[gazetteer|llm_fallback|none], city: Optional[str])
- [x] T010 [P] Create `app/schemas/cluster.py` — `ClusterInfo` model (cluster_id: Optional[str], is_duplicate: bool, cluster_size: Optional[int], cluster_weight: Optional[float], similarity_score: Optional[float])
- [x] T011 [P] Create `app/schemas/analytics.py` — `AnalyticsQuery` model (region: str="all", days: int=7 range 1-90, department: str="all"), `ClusterSummary` model, and `AnalyticsSummary` response model per contracts/analytics.md
- [x] T012 [P] Create `app/schemas/__init__.py` — Re-export all schema classes for convenient imports
- [x] T013 Create `app/data/departments.json` — Department taxonomy with 10 entries: water_supply, electricity, roads, sanitation, police, health, education, revenue, gas, telecom. Each with id, name_en, name_ur, sub_categories list, and response_template_ur
- [x] T014 [P] Create `app/data/pakistan_gazetteer.json` — Gazetteer with ~50 entries covering Islamabad sectors (F-6 through I-10), Lahore areas (Gulberg, DHA, Johar Town), Karachi areas (Clifton, Nazimabad, Korangi), and major landmarks. Each with name, aliases, city, lat, lon
- [x] T015 [P] Create `app/data/response_templates.json` — Urdu response templates keyed by department (10 entries), each with acknowledgment text in Urdu script
- [x] T016 Create `app/main.py` — FastAPI app with lifespan context manager (init httpx.AsyncClient, load config, placeholder for pipeline init), CORS middleware with explicit origins, error exception handlers mapping NaqsKARException to JSON responses, include v1 router. App MUST start with `uvicorn app.main:app` and serve `/health`

**Checkpoint**: Foundation ready — `uvicorn app.main:app` starts, `/health` returns basic status, all schemas importable, data files loadable.

---

## Phase 3: User Story 1 — Single Complaint Classification (Priority: P1) 🎯 MVP

**Goal**: A single raw complaint → full structured JSON response (department, urgency, geo, cluster, Urdu response)

**Independent Test**: `curl -X POST http://localhost:8000/api/v1/classify -H "Content-Type: application/json" -d '{"text": "pani nahi araha 4 din se G-9 mein"}'` returns a complete ClassifyResponse

### Normalizer Module

- [x] T017 Create `app/modules/normalizer/protocol.py` — `NormalizerProtocol` ABC with abstract async method `process(request: ClassifyRequest) -> NormalizedComplaint` where `NormalizedComplaint` is a Pydantic model with fields: original_text, normalized_text, detected_language, extracted_intent, extracted_entities (dict), confidence (float)
- [x] T018 Create `app/modules/normalizer/llm_strategy.py` — `LLMNormalizer(NormalizerProtocol)` that uses `httpx.AsyncClient` to call Claude API with a few-shot system prompt (5-8 examples of Roman Urdu / Urdu / English → structured intent). Must output JSON. Include fallback to return raw text with low confidence if LLM fails
- [x] T019 [P] [US1] Create `app/modules/normalizer/__main__.py` — Standalone demo: creates LLMNormalizer, runs 3 sample complaints (Roman Urdu, Urdu script, English), prints results. Runnable via `python -m app.modules.normalizer`
- [x] T020 [P] [US1] Create `app/modules/normalizer/__init__.py` — Factory function `create_normalizer(config: Settings) -> NormalizerProtocol` that returns the strategy based on `config.normalizer_strategy`

### Classifier Module

- [x] T021 [US1] Create `app/modules/classifier/protocol.py` — `ClassifierProtocol` ABC with abstract async method `classify(normalized: NormalizedComplaint) -> ClassificationResult`
- [x] T022 [US1] Create `app/modules/classifier/keyword_urgency.py` — `UrgencyBooster` class with a hardcoded list of urgency keywords (baccha, hospital, khoon, aag, zakhmi, ambulance, maut, emergency, etc.) in Roman Urdu and English. Method `boost(result: ClassificationResult, original_text: str) -> ClassificationResult` sets urgency_score to max(current, 0.8) if any keyword found
- [x] T023 [US1] Create `app/modules/classifier/llm_strategy.py` — `LLMClassifier(ClassifierProtocol)` that calls Claude API with few-shot prompt to classify department (from departments.json taxonomy), sub_category, urgency_score, sentiment. Post-processes with UrgencyBooster. Fallback: keyword-only classification with low confidence
- [x] T024 [P] [US1] Create `app/modules/classifier/__main__.py` — Standalone demo with 4 sample inputs including one urgency-keyword test. Runnable via `python -m app.modules.classifier`
- [x] T025 [P] [US1] Create `app/modules/classifier/__init__.py` — Factory function `create_classifier(config) -> ClassifierProtocol`

### Geo-Extractor Module

- [x] T026 [US1] Create `app/modules/geo_extractor/protocol.py` — `GeoExtractorProtocol` ABC with abstract async method `extract(text: str, location_hint: Optional[str]) -> Optional[LocationResult]`
- [x] T027 [US1] Create `app/modules/geo_extractor/gazetteer.py` — `Gazetteer` class that loads `app/data/pakistan_gazetteer.json`, provides `lookup(text: str) -> Optional[GazetteerEntry]` using substring matching against name and all aliases (case-insensitive)
- [x] T028 [US1] Create `app/modules/geo_extractor/llm_strategy.py` — `LLMGeoExtractor(GeoExtractorProtocol)` that first tries gazetteer lookup; if no match, calls Claude API to extract and resolve location from text. Returns LocationResult with source=gazetteer or source=llm_fallback. Fallback: return None if both fail
- [x] T029 [P] [US1] Create `app/modules/geo_extractor/__main__.py` — Standalone demo with 3 samples: exact match ("G-9"), fuzzy match ("G nain"), no location. Runnable via `python -m app.modules.geo_extractor`
- [x] T030 [P] [US1] Create `app/modules/geo_extractor/__init__.py` — Factory function `create_geo_extractor(config) -> GeoExtractorProtocol`

### Orchestrator & Route

- [x] T031 [US1] Create `app/orchestrator/pipeline.py` — `ComplaintPipeline` class that wires normalizer → classifier → geo_extractor in sequence (normalizer + geo_extractor can run in parallel via `asyncio.gather()`). Method `async process(request: ClassifyRequest) -> ClassifyResponse`. Loads response templates from `app/data/response_templates.json`. Sets `cluster=None` (dedup wired in US3). Measures processing_time_ms
- [x] T032 [US1] Create `app/api/v1/routes.py` — `POST /api/v1/classify` async endpoint that takes ClassifyRequest body, calls pipeline.process(), returns ClassifyResponse. Structured error handling with request_id logging
- [x] T033 [US1] Create `app/api/v1/health.py` — `GET /health` endpoint returning module status, strategy names, LLM provider connectivity, uptime. Import as router in main.py
- [x] T034 [US1] Wire pipeline into `app/main.py` lifespan — instantiate all module factories using config, create ComplaintPipeline, store on `app.state`. Include API v1 routers. Verify full end-to-end: start server → POST /classify → get ClassifyResponse

**Checkpoint**: User Story 1 is fully functional. `POST /api/v1/classify` accepts multilingual text and returns department, urgency, geo, and Urdu response. The single `/classify` endpoint is the MVP.

---

## Phase 4: User Story 2 — Batch Complaint Processing (Priority: P2)

**Goal**: Submit up to 100 complaints in one request, get per-item results with partial failure support

**Independent Test**: `curl -X POST http://localhost:8000/api/v1/batch-classify` with 5 complaints returns 5 results

- [ ] T035 [US2] Create `BatchClassifyResponse` model in `app/schemas/classification.py` — Add `BatchItemResult` (index: int, status: success|error, classification: Optional, location: Optional, cluster: Optional, suggested_response_urdu: Optional, error: Optional[ErrorResponse]) and `BatchClassifyResponse` (schema_version, request_id, total, successful, failed, results: list[BatchItemResult], processing_time_ms)
- [ ] T036 [US2] Add `async batch_process(requests: list[ClassifyRequest]) -> BatchClassifyResponse` method to `app/orchestrator/pipeline.py` — Processes each complaint via `asyncio.gather()` with `return_exceptions=True`. Catches per-item errors and wraps them in BatchItemResult with status=error. Never fails the entire batch
- [ ] T037 [US2] Add `POST /api/v1/batch-classify` endpoint in `app/api/v1/routes.py` — Takes BatchClassifyRequest, calls pipeline.batch_process(), returns BatchClassifyResponse. Validates batch size (1-100) at Pydantic level

**Checkpoint**: User Stories 1 AND 2 both work independently. Batch endpoint processes mixed-language complaints with per-item error handling.

---

## Phase 5: User Story 3 — Semantic Deduplication & Clustering (Priority: P3)

**Goal**: Semantically similar complaints near the same location within 7 days are clustered together

**Independent Test**: POST 5 similar water complaints for G-9 → all get the same `cluster_id` with weight = count × avg_urgency

- [ ] T038 [US3] Create `app/modules/deduplication/protocol.py` — `DeduplicatorProtocol` ABC with abstract async method `deduplicate(text: str, classification: ClassificationResult, location: Optional[LocationResult]) -> Optional[ClusterInfo]`
- [ ] T039 [US3] Create `app/modules/deduplication/store.py` — `InMemoryClusterStore` class with rolling-window buffer. Stores: embedding vector, classification, location, timestamp per complaint. Methods: `add(entry)`, `find_cluster(embedding, location, config) -> Optional[ClusterInfo]`, `prune_expired()`. Clusters by cosine similarity ≤ 0.3 AND haversine distance ≤ 500m AND within 7 days
- [ ] T040 [US3] Create `app/modules/deduplication/embedding_strategy.py` — `EmbeddingDeduplicator(DeduplicatorProtocol)` that loads `paraphrase-multilingual-MiniLM-L12-v2` via sentence-transformers (in lifespan), embeds text via `asyncio.to_thread()`, queries InMemoryClusterStore for matching cluster, creates new cluster if none found. Returns ClusterInfo
- [ ] T041 [P] [US3] Create `app/modules/deduplication/__main__.py` — Standalone demo: creates 5 similar complaints + 2 different ones, shows clustering results. Runnable via `python -m app.modules.deduplication`
- [ ] T042 [P] [US3] Create `app/modules/deduplication/__init__.py` — Factory function `create_deduplicator(config) -> Optional[DeduplicatorProtocol]` returning None if strategy is `none`
- [ ] T043 [US3] Wire deduplication into `app/orchestrator/pipeline.py` — After classification + geo extraction, call deduplicator.deduplicate() if deduplicator is not None. Set cluster field on ClassifyResponse. If dedup fails, set cluster=None and add warning to _warnings list

**Checkpoint**: All three backend user stories work. Similar complaints cluster together. Dedup gracefully degrades if embedding model fails.

---

## Phase 6: User Story 4 — Analytics & Heatmap Data (Priority: P4)

**Goal**: Query aggregated complaint data by region, department, and time range

**Independent Test**: `curl http://localhost:8000/api/v1/analytics?region=Islamabad&days=7` returns department counts and cluster coordinates

- [ ] T044 [US4] Create `app/orchestrator/complaint_store.py` — `InMemoryComplaintStore` class that stores processed ClassifyResponse entries in memory. Methods: `add(response: ClassifyResponse)`, `query(region: Optional[str], days: int, department: Optional[str]) -> list[ClassifyResponse]`, `get_analytics(query: AnalyticsQuery) -> AnalyticsSummary`. Computes by_department counts, by_urgency bands (low ≤0.3, medium ≤0.6, high ≤0.8, critical >0.8), avg_urgency, and active cluster summaries
- [ ] T045 [US4] Wire complaint store into pipeline — After processing each complaint in `pipeline.process()`, store the result in InMemoryComplaintStore. Initialize store in lifespan
- [ ] T046 [US4] Add `GET /api/v1/analytics` endpoint in `app/api/v1/routes.py` — Takes AnalyticsQuery as query params, calls complaint_store.get_analytics(), returns AnalyticsSummary. Returns empty result (zero counts, empty clusters) when no data matches — never an error

**Checkpoint**: Analytics endpoint returns live aggregated data from complaints processed during the session.

---

## Phase 7: User Story 5 — Public Heatmap Dashboard (Priority: P5)

**Goal**: Live filterable map showing clustered complaints by location and department

**Independent Test**: Open `http://localhost:3000`, see Leaflet map with cluster markers, filter by department

- [ ] T047 [US5] Create `dashboard/index.html` — HTML page with Leaflet.js (CDN), filter controls (department dropdown, days slider), and a complaint count summary bar. Links to app.js and style.css. Uses OpenStreetMap tiles
- [ ] T048 [US5] Create `dashboard/app.js` — Fetches `/api/v1/analytics` on load and on filter change. Renders cluster markers on Leaflet map with color-coded by department, size-scaled by weight, popups showing representative_text and complaint_count. Updates summary bar with total_complaints and by_department counts. Auto-refreshes every 30 seconds
- [ ] T049 [P] [US5] Create `dashboard/style.css` — Dark theme styling for the dashboard: navy/dark-gray background, white text, glassmorphism filter panel, smooth marker animations, responsive layout for desktop. NaqsKAR branding header with green accent (Pakistan flag green #01411C)
- [ ] T050 [US5] Add CORS origin for dashboard (localhost:3000) in `app/main.py` and add static file serving or document the `python -m http.server 3000 --directory dashboard` approach in a comment

**Checkpoint**: Full end-to-end demo: POST complaints via API → see them appear on the heatmap dashboard with filtering.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Demo preparation and production hardening

- [ ] T051 [P] Create `app/data/sample_complaints.json` — 15-20 sample complaints for demo: 5 Roman Urdu (water, electricity, roads), 3 Urdu script, 3 English, 2 code-mixed, 2 high-urgency (medical/fire), 5 duplicate cluster (same issue, nearby locations)
- [ ] T052 [P] Create `scripts/seed_demo.py` — Script that reads sample_complaints.json and POSTs each to `/api/v1/classify` with 1-second delays, seeding the analytics store for demo. Prints results summary
- [ ] T053 Create `Dockerfile` — Multi-stage build: stage 1 installs deps, stage 2 copies app. Exposes PORT, runs uvicorn. Includes healthcheck
- [ ] T054 [P] Create `docker-compose.yml` — Single service for the API (port 8000). Mount .env. Optional dashboard service (nginx or python http.server on port 3000)
- [ ] T055 Update `README.md` — Add quickstart instructions matching quickstart.md, architecture diagram from plan.md, API examples from contracts
- [ ] T056 Run full end-to-end validation — Start server, run seed_demo.py, verify: (1) /health returns healthy, (2) single classify works for Roman Urdu + English + Urdu, (3) batch classify processes 5 complaints, (4) analytics returns data, (5) dashboard shows clusters on map. Fix any issues found

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — this is the MVP
- **US2 (Phase 4)**: Depends on US1 (extends pipeline with batch method)
- **US3 (Phase 5)**: Depends on US1 (adds dedup module to pipeline)
- **US4 (Phase 6)**: Depends on US1 (adds complaint store + analytics endpoint)
- **US5 (Phase 7)**: Depends on US4 (dashboard consumes analytics API)
- **Polish (Phase 8)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories ← **MVP**
- **US2 (P2)**: Can start after US1 — Extends pipeline, independently testable
- **US3 (P3)**: Can start after US1 — Adds module, independently testable
- **US4 (P4)**: Can start after US1 — Adds store + endpoint, independently testable
- **US5 (P5)**: Can start after US4 — Consumes analytics API

### Within Each User Story

- Protocol/ABC before strategy implementation
- Strategy before factory function
- Factory before orchestrator wiring
- Orchestrator before API endpoint
- `__main__.py` demos can be parallel with everything (they're standalone)

### Parallel Opportunities

- T003 + T004 (config files — different files)
- T007 + T008 + T009 + T010 + T011 + T012 (all schema files — independent)
- T013 + T014 + T015 (data files — independent)
- T019 + T020 (normalizer __main__ + __init__ — different files)
- T024 + T025 (classifier __main__ + __init__ — different files)
- T029 + T030 (geo __main__ + __init__ — different files)
- T041 + T042 (dedup __main__ + __init__ — different files)
- T047 + T049 (dashboard HTML + CSS — different files)
- T051 + T052 + T053 + T054 (polish tasks — independent files)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `POST /api/v1/classify` with Roman Urdu input → get full response
5. Deploy/demo if ready — this alone is a working product

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test → Deploy/Demo (**MVP!** — single classify works)
3. Add US2 → Test → Deploy/Demo (batch added)
4. Add US3 → Test → Deploy/Demo (dedup + clustering)
5. Add US4 → Test → Deploy/Demo (analytics API)
6. Add US5 → Test → Deploy/Demo (heatmap dashboard — full product)

### Hackathon Day Mapping

- **Day 1 evening**: Complete Phase 1 + Phase 2 + start Phase 3 (T001–T020)
- **Day 2**: Complete Phase 3 (US1 MVP) + Phase 4 (US2) + Phase 5 (US3) — target 75%+ for midway eval
- **Day 3**: Complete Phase 6 (US4) + Phase 7 (US5) + Phase 8 (polish + demo prep)
