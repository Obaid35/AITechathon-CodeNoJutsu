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

from app.core.config import Settings, get_settings
from app.core.errors import NaqsKARException
from app.core.logging import generate_request_id, get_logger, setup_logging

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: init resources on startup, cleanup on shutdown."""
    settings = get_settings()
    setup_logging(debug=settings.debug)

    logger.info("naqskar_starting", host=settings.host, port=settings.port)

    # Shared HTTP client for LLM API calls
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    app.state.settings = settings
    app.state.start_time = time.time()

    # Pipeline will be initialized here once modules are wired (Phase 3)
    app.state.pipeline = None
    app.state.complaint_store = None

    logger.info("naqskar_ready")
    yield

    # Shutdown
    await app.state.http_client.aclose()
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
# These imports are here to avoid circular imports with app.state
from app.api.v1.health import router as health_router  # noqa: E402

app.include_router(health_router)

# v1 routes will be included once they exist (Phase 3)
# from app.api.v1.routes import router as v1_router
# app.include_router(v1_router, prefix="/api/v1")
