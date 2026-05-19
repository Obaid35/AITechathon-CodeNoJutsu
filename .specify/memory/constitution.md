<!--
  SYNC IMPACT REPORT
  ==================================
  Version change: 0.0.0 → 1.0.0
  Bump rationale: MAJOR — initial constitution ratification

  Modified principles: N/A (initial creation)

  Added sections:
  - Core Principles (6 principles)
  - Technology & Architecture Constraints
  - Development Workflow
  - Governance

  Removed sections: None

  Templates requiring updates:
  ✅ plan-template.md — Constitution Check section aligns with principles
  ✅ spec-template.md — User stories support independent demoability (Principle II)
  ✅ tasks-template.md — Phase structure supports incremental delivery (Principle I)

  Follow-up TODOs: None
-->

# NaqsKAR Constitution

## Core Principles

### I. End-to-End Working System

Every feature MUST ship as a working end-to-end pipeline before
any horizontal expansion occurs. A thin vertical slice that
processes a complaint from raw text → classification → routing
response is worth more than five half-built modules.

- **No dead-end code**: Every committed module MUST be reachable
  from at least one API endpoint.
- **Demo at every merge**: Each pull request MUST leave the system
  in a runnable state where `uvicorn app.main:app` starts without
  error and at least one endpoint returns a valid response.
- **Incremental completeness**: Add depth (more languages, more
  departments, better accuracy) only after the full pipeline works.

### II. Modular Demoability

Each core module (Normalizer, Classifier, Geo-Extractor,
Deduplication Engine, Router) MUST be independently demonstrable.

- **Standalone invocation**: Every module MUST expose a function
  that accepts a plain Python dict/Pydantic model and returns one,
  with zero dependency on FastAPI request context.
- **Module-level `__main__`**: Each module file MUST include a
  `if __name__ == "__main__"` block or a CLI entry point that runs
  a self-contained demo with sample input.
- **Isolation guarantee**: Module A MUST NOT import from Module B
  unless that dependency is declared in the architecture diagram.
  Cross-module communication goes through the orchestration layer.

### III. Async-First FastAPI

All I/O-bound operations MUST use `async`/`await`. CPU-bound ML
inference MUST be offloaded to thread/process pools so the event
loop is never blocked.

- **Route handlers**: All FastAPI route functions MUST be declared
  `async def`.
- **LLM / external API calls**: MUST use `httpx.AsyncClient` or
  the provider SDK's async interface. Synchronous `requests` calls
  are prohibited in route-reachable code paths.
- **ML inference**: Heavy model calls (transformers, embeddings)
  MUST be wrapped in `asyncio.to_thread()` or dispatched to a
  `ProcessPoolExecutor` to prevent event-loop starvation.
- **Startup/shutdown**: Model loading, DB connections, and
  expensive initializations MUST use FastAPI lifespan events, not
  module-level globals.

### IV. Contract-Driven JSON

Every module boundary MUST be defined by a typed Pydantic schema.
These schemas are the single source of truth for what flows
between components.

- **Pydantic v2 models**: All request bodies, response bodies, and
  inter-module payloads MUST be Pydantic `BaseModel` subclasses
  with explicit field types and `model_config` where needed.
- **No raw dicts at boundaries**: Functions that cross module
  boundaries MUST accept and return typed models, never `dict` or
  `Any`.
- **Versioned contracts**: API response models MUST carry a
  `schema_version` field (e.g., `"1.0"`). Breaking changes to a
  schema MUST increment the major version and be documented.
- **Example fixtures**: Each schema MUST include a
  `model_config = ConfigDict(json_schema_extra={"examples": [...]})`
  block so that `/docs` renders usable examples.

### V. Swappable ML Layer

All ML/AI logic MUST be accessed through a strategy interface so
that the underlying implementation can change from few-shot LLM
prompting to fine-tuned models without touching the orchestration
or API layers.

- **Strategy pattern**: Each ML capability (normalization,
  classification, geo-extraction) MUST define an abstract base
  class (Python `Protocol` or `ABC`) with a `predict` / `process`
  method.
- **Runtime selection**: The active strategy MUST be selectable via
  environment variable or configuration file, not hard-coded
  imports.
- **LLM-first default**: The initial implementation MUST use
  few-shot LLM prompting (Claude API or Ollama) so the system
  works without training data.
- **Drop-in upgrade path**: When a fine-tuned model is ready, it
  MUST be deployable by implementing the same Protocol and changing
  one config value. Zero orchestration code changes allowed.
- **Fallback chain**: If the primary strategy fails (API timeout,
  model OOM), the system MUST attempt a fallback strategy before
  returning an error.

### VI. Production-Grade API Quality

NaqsKAR is an API service, not a notebook. Every endpoint MUST
meet production standards even during hackathon development.

- **Structured error responses**: All errors MUST return a JSON
  body with `error_code`, `message`, and `details` fields. No
  raw stack traces in non-debug mode.
- **Request validation**: All endpoints MUST validate input via
  Pydantic and return `422` with field-level errors on failure.
- **Health check**: A `GET /health` endpoint MUST exist and return
  system status including model-load state.
- **Logging**: All module entries/exits MUST emit structured JSON
  logs with `request_id`, `module`, `duration_ms`, and `status`.
- **CORS & security headers**: CORS MUST be configured explicitly
  (no wildcard `*` in production). Security headers (CSP, HSTS)
  MUST be present.

## Technology & Architecture Constraints

- **Language**: Python 3.9+ (target 3.11 for production)
- **Framework**: FastAPI with Uvicorn ASGI server
- **ML/NLP**: Hugging Face Transformers, sentence-transformers,
  scikit-learn for clustering
- **LLM**: Claude API (primary) with Ollama (local fallback)
- **Data validation**: Pydantic v2
- **HTTP client**: httpx (async)
- **Testing**: pytest with pytest-asyncio
- **Containerization**: Docker with multi-stage builds
- **Environment**: python-dotenv for local, env vars for production
- **No ORM required**: Start with in-memory stores or flat files;
  add a database only when persistence is a proven need.

## Development Workflow

- **Branch strategy**: Feature branches off `zohaib-dev`, merge via
  PR with at least a self-review checklist.
- **Commit discipline**: Each commit MUST leave the app startable.
  Use conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`).
- **Module-first development**: Build and demo each module in
  isolation before wiring it into the pipeline.
- **Contract-first integration**: Define Pydantic schemas for
  inter-module communication before writing implementation code.
- **Checkpoint validation**: After completing each module, verify
  the full pipeline still runs end-to-end.

## Governance

- This constitution is the supreme authority for all NaqsKAR
  development decisions. Conflicts between this document and any
  other guidance MUST be resolved in favor of this constitution.
- Amendments require: (1) a written proposal documenting the
  change, (2) rationale explaining why the existing principle is
  insufficient, and (3) an update to this file with a version bump.
- Version follows semantic versioning: MAJOR for principle
  removals/redefinitions, MINOR for new principles or material
  expansions, PATCH for wording clarifications.
- All code reviews MUST verify compliance with these principles.
  Non-compliant code MUST NOT be merged without a documented
  exception in the Complexity Tracking section of the plan.

**Version**: 1.0.0 | **Ratified**: 2026-05-20 | **Last Amended**: 2026-05-20
