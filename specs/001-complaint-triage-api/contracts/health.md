# Contract: GET /health

**Version**: 1.0
**Module**: Infrastructure
**User Story**: Cross-cutting (FR-009)

## Request

**Method**: `GET`
**Path**: `/health`

No query parameters or request body.

## Response — 200 OK (Healthy)

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "modules": {
    "normalizer": {
      "status": "ready",
      "strategy": "llm_claude",
      "last_success": "2026-05-20T10:29:55Z"
    },
    "classifier": {
      "status": "ready",
      "strategy": "llm_claude",
      "last_success": "2026-05-20T10:29:55Z"
    },
    "geo_extractor": {
      "status": "ready",
      "strategy": "llm_gazetteer",
      "gazetteer_entries": 487,
      "last_success": "2026-05-20T10:29:50Z"
    },
    "deduplication": {
      "status": "ready",
      "strategy": "embedding_dbscan",
      "model_loaded": true,
      "active_clusters": 12,
      "buffer_size": 156
    }
  },
  "llm_providers": {
    "primary": {
      "name": "claude",
      "status": "connected",
      "last_latency_ms": 850
    },
    "fallback": {
      "name": "ollama",
      "status": "connected",
      "last_latency_ms": 1200
    }
  }
}
```

## Response — 200 OK (Degraded)

```json
{
  "status": "degraded",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "modules": {
    "normalizer": {"status": "ready", "strategy": "llm_claude"},
    "classifier": {"status": "ready", "strategy": "llm_claude"},
    "geo_extractor": {"status": "ready", "strategy": "llm_gazetteer"},
    "deduplication": {
      "status": "unavailable",
      "strategy": "embedding_dbscan",
      "model_loaded": false,
      "error": "sentence-transformers model failed to load: CUDA OOM"
    }
  },
  "llm_providers": {
    "primary": {"name": "claude", "status": "connected"},
    "fallback": {"name": "ollama", "status": "disconnected", "error": "Connection refused"}
  },
  "_warnings": [
    "Deduplication module unavailable — clustering disabled",
    "Fallback LLM provider disconnected — no failover available"
  ]
}
```

## Response — 503 Service Unavailable

Returned only when no ML providers are available AND no fallback is possible.

```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "modules": {
    "normalizer": {"status": "unavailable"},
    "classifier": {"status": "unavailable"},
    "geo_extractor": {"status": "unavailable"},
    "deduplication": {"status": "unavailable"}
  },
  "llm_providers": {
    "primary": {"name": "claude", "status": "disconnected"},
    "fallback": {"name": "ollama", "status": "disconnected"}
  }
}
```
