"""NaqsKAR — FastAPI application entry point.

Constitution III: Lifespan events for init. All routes async def.
Constitution VI: CORS configured explicitly, structured error handlers.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import NaqsKARException
from app.core.logging import generate_request_id, get_logger, setup_logging
from app.modules.classifier import create_classifier
from app.modules.geo_extractor import create_geo_extractor
from app.modules.normalizer import create_normalizer
from app.orchestrator.pipeline import ComplaintPipeline

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: init resources on startup, cleanup on shutdown."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

    logger.info("naqskar_starting", host=settings.host, port=settings.port)

    # Shared HTTP client for LLM API calls
    http_client = httpx.AsyncClient(timeout=30.0)
    app.state.http_client = http_client
    app.state.settings = settings
    app.state.start_time = time.time()

    # Initialize ML modules via factories (Constitution V)
    normalizer = create_normalizer(settings, http_client)
    classifier = create_classifier(settings, http_client)
    geo_extractor = create_geo_extractor(settings, http_client)

    # Wire pipeline (Constitution I: end-to-end working system)
    app.state.pipeline = ComplaintPipeline(
        normalizer=normalizer,
        classifier=classifier,
        geo_extractor=geo_extractor,
        deduplicator=None,  # Wired in Phase 5 (US3)
    )

    # Complaint store for analytics (wired in Phase 6 / US4)
    app.state.complaint_store = None

    logger.info(
        "naqskar_ready",
        normalizer=type(normalizer).__name__,
        classifier=type(classifier).__name__,
        geo=type(geo_extractor).__name__ if geo_extractor else "disabled",
    )
    yield

    # Shutdown
    await http_client.aclose()
    logger.info("naqskar_shutdown")


app = FastAPI(
    title="NaqsKAR",
    description="AI-Powered Citizen Complaint Triage & Routing for Pakistan",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS (Constitution VI: explicit origins, no wildcard in production) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Error Handlers ---


@app.exception_handler(NaqsKARException)
async def naqskar_exception_handler(
    request: Request, exc: NaqsKARException
) -> JSONResponse:
    """Handle all NaqsKAR domain exceptions as structured JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response().model_dump(),
    )


# --- Request ID Middleware ---


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Generate request_id for every request and add to response headers."""
    rid = generate_request_id()
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


# --- Import and include routers ---
from app.api.v1.health import router as health_router  # noqa: E402
from app.api.v1.routes import router as v1_router  # noqa: E402

app.include_router(health_router)
app.include_router(v1_router)
