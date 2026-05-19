"""Health check endpoint.

Constitution VI: GET /health MUST return system status including model-load state.
"""

import time

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Return system health status including module readiness."""
    settings = request.app.state.settings
    start_time = getattr(request.app.state, "start_time", time.time())
    pipeline = getattr(request.app.state, "pipeline", None)

    # Module status
    modules = {}
    if pipeline:
        for name, module in pipeline.get_module_status().items():
            modules[name] = module
    else:
        modules = {
            "normalizer": {"status": "not_initialized"},
            "classifier": {"status": "not_initialized"},
            "geo_extractor": {"status": "not_initialized"},
            "deduplication": {"status": "not_initialized"},
        }

    # Determine overall status
    statuses = [m.get("status", "unknown") for m in modules.values()]
    if all(s == "ready" for s in statuses):
        overall = "healthy"
    elif any(s == "ready" for s in statuses):
        overall = "degraded"
    elif pipeline is None:
        overall = "initializing"
    else:
        overall = "unhealthy"

    return {
        "status": overall,
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - start_time),
        "modules": modules,
        "llm_providers": {
            "primary": {
                "name": settings.app_llm_provider.value,
                "status": "configured",
            },
        },
    }
