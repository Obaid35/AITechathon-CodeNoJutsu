# Implementation Plan: NaqsKAR — AI Complaint Triage & Routing API

**Branch**: `001-complaint-triage-api` | **Date**: 2026-05-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-complaint-triage-api/spec.md`

## Summary

NaqsKAR is an async FastAPI service that accepts citizen complaints in Roman Urdu, Urdu script, or English and returns structured JSON containing department classification, urgency score, geo-resolved location, semantic cluster assignment, and a suggested Urdu response template. The architecture uses a strategy-pattern ML layer (few-shot LLM now, fine-tuned models later) with Pydantic v2 contracts at every module boundary. Five independently demoable modules — Normalizer, Classifier, Geo-Extractor, Deduplicator, and Router — are wired through a pipeline orchestrator.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI 0.100+, Pydantic v2, httpx, sentence-transformers, scikit-learn, anthropic SDK (Claude), uvicorn
**Storage**: In-memory stores for MVP (rolling-window deduplication buffer, complaint history for analytics). No database required for hackathon.
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server / Docker container (local dev on Windows)
**Project Type**: Web service (API backend + lightweight dashboard frontend)
**Performance Goals**: <3s single classify, <60s for batch of 100, dashboard load <5s
**Constraints**: Stateless API (no persistent DB for MVP), LLM API latency is the bottleneck, must handle provider outages gracefully
**Scale/Scope**: Hackathon demo with ~50 gold-set complaints, 8–12 department taxonomy, single-tenant

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I | End-to-End Working System | ✅ PASS | Plan builds US1 (single classify) as complete vertical slice before any other story. Every module is reachable from `/api/v1/classify`. |
| II | Modular Demoability | ✅ PASS | Each module dir has `protocol.py` (ABC), strategy implementation, and `__main__.py` for standalone demo. Modules communicate only through orchestrator. |
| III | Async-First FastAPI | ✅ PASS | All route handlers are `async def`. LLM calls use `httpx.AsyncClient`. ML inference wrapped in `asyncio.to_thread()`. Lifespan events for init. |
| IV | Contract-Driven JSON | ✅ PASS | `app/schemas/` contains Pydantic v2 models for all request/response bodies and inter-module payloads. `schema_version` on responses. `json_schema_extra` examples on all models. |
| V | Swappable ML Layer | ✅ PASS | Each ML module defines a `Protocol` ABC. LLM strategy is default. Config selects strategy at runtime via `APP_NORMALIZER_STRATEGY`, etc. Fallback chain implemented. |
| VI | Production-Grade API Quality | ✅ PASS | Structured error handler, `/health` endpoint, structured JSON logging with `request_id`, explicit CORS config. |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-complaint-triage-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── classify.md
│   ├── batch-classify.md
│   ├── analytics.md
│   └── health.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py                        # FastAPI app, lifespan, CORS, error handlers
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── routes.py              # /classify, /batch-classify, /analytics
│       └── health.py              # /health
├── core/
│   ├── __init__.py
│   ├── config.py                  # pydantic-settings: env vars, strategy selection
│   ├── logging.py                 # Structured JSON logger with request_id
│   └── errors.py                  # ErrorResponse model, exception handlers
├── schemas/
│   ├── __init__.py
│   ├── complaint.py               # ClassifyRequest, BatchClassifyRequest
│   ├── classification.py          # ClassificationResult, ClassifyResponse, BatchResponse
│   ├── location.py                # LocationResult
│   ├── cluster.py                 # ClusterInfo
│   └── analytics.py               # AnalyticsQuery, AnalyticsSummary
├── modules/
│   ├── __init__.py
│   ├── normalizer/
│   │   ├── __init__.py
│   │   ├── protocol.py            # NormalizerProtocol (ABC)
│   │   ├── llm_strategy.py        # Few-shot LLM normalizer (default)
│   │   └── __main__.py            # Standalone demo
│   ├── classifier/
│   │   ├── __init__.py
│   │   ├── protocol.py            # ClassifierProtocol (ABC)
│   │   ├── llm_strategy.py        # Few-shot LLM classifier (default)
│   │   ├── keyword_urgency.py     # Urgency keyword boost logic
│   │   └── __main__.py            # Standalone demo
│   ├── geo_extractor/
│   │   ├── __init__.py
│   │   ├── protocol.py            # GeoExtractorProtocol (ABC)
│   │   ├── llm_strategy.py        # LLM + gazetteer geo extraction
│   │   ├── gazetteer.py           # Pakistan gazetteer lookup (JSON)
│   │   └── __main__.py            # Standalone demo
│   └── deduplication/
│       ├── __init__.py
│       ├── protocol.py            # DeduplicatorProtocol (ABC)
│       ├── embedding_strategy.py  # sentence-transformers + clustering
│       ├── store.py               # In-memory rolling-window store
│       └── __main__.py            # Standalone demo
├── orchestrator/
│   ├── __init__.py
│   └── pipeline.py                # Wires all modules: normalize → classify → geo → dedup → route
└── data/
    ├── pakistan_gazetteer.json     # Districts, sectors, tehsils, landmarks
    ├── departments.json           # Department taxonomy
    └── response_templates.json    # Urdu response templates by department

dashboard/                         # Lightweight heatmap frontend
├── index.html
├── app.js
└── style.css

tests/
├── conftest.py
├── unit/
│   ├── test_normalizer.py
│   ├── test_classifier.py
│   ├── test_geo_extractor.py
│   └── test_deduplication.py
├── integration/
│   └── test_pipeline.py
└── contract/
    ├── test_classify_endpoint.py
    └── test_batch_endpoint.py
```

**Structure Decision**: Single-project backend (FastAPI under `app/`) with a lightweight static frontend (`dashboard/`). No Next.js for the hackathon — a plain HTML/JS/CSS dashboard with Leaflet is faster to ship and avoids a Node.js build step. The frontend consumes the same `/api/v1/analytics` endpoint.

## Complexity Tracking

> No violations to justify — all Constitution checks pass.
