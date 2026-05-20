"""API v1 routes — classify and batch-classify endpoints.

Constitution III: All route handlers are async def.
Constitution IV: Pydantic models for all request/response bodies.
Constitution VI: Structured errors with request_id.
"""

from fastapi import APIRouter, Query, Request

from app.core.errors import NaqsKARException
from app.core.logging import get_logger
from app.schemas.analytics import AnalyticsQuery, AnalyticsSummary
from app.schemas.classification import BatchClassifyResponse, ClassifyResponse
from app.schemas.complaint import BatchClassifyRequest, ClassifyRequest

logger = get_logger("api.v1")

router = APIRouter(prefix="/api/v1", tags=["classification"])


@router.post("/classify", response_model=ClassifyResponse)
async def classify_complaint(
    request: Request,
    body: ClassifyRequest,
) -> ClassifyResponse:
    """Classify a single citizen complaint.

    Accepts Roman Urdu, Urdu script, or English text and returns
    structured classification with department, urgency, geo-location,
    and suggested Urdu response.
    """
    pipeline = request.app.state.pipeline
    if pipeline is None:
        raise NaqsKARException(
            error_code="PIPELINE_NOT_READY",
            message="Classification pipeline is not initialized yet",
            status_code=503,
        )

    request_id = getattr(request.state, "request_id", "unknown")
    logger.info("classify_start", request_id=request_id, text_length=len(body.text))

    result = await pipeline.process(body, request_id=request_id)

    logger.info(
        "classify_complete",
        request_id=request_id,
        department=result.classification.department,
        duration_ms=result.processing_time_ms,
    )

    return result


@router.post("/batch-classify", response_model=BatchClassifyResponse)
async def batch_classify_complaints(
    request: Request,
    body: BatchClassifyRequest,
) -> BatchClassifyResponse:
    """Classify a batch of citizen complaints (max 100).

    Each complaint is processed independently. Individual failures
    do not affect other items in the batch.
    """
    pipeline = request.app.state.pipeline
    if pipeline is None:
        raise NaqsKARException(
            error_code="PIPELINE_NOT_READY",
            message="Classification pipeline is not initialized yet",
            status_code=503,
        )

    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "batch_classify_start",
        request_id=request_id,
        batch_size=len(body.complaints),
    )

    result = await pipeline.batch_process(body.complaints, request_id=request_id)

    logger.info(
        "batch_classify_complete",
        request_id=request_id,
        total=result.total,
        successful=result.successful,
        failed=result.failed,
        duration_ms=result.processing_time_ms,
    )

    return result


@router.get("/analytics", response_model=AnalyticsSummary)
async def get_analytics(
    request: Request,
    region: str = Query("all", description="City/region filter"),
    days: int = Query(7, ge=1, le=90, description="Time window in days"),
    department: str = Query("all", description="Department filter"),
) -> AnalyticsSummary:
    """Get aggregated analytics from processed complaints.

    Returns department counts, urgency bands, and active cluster
    summaries with coordinates for heatmap rendering.
    """
    store = request.app.state.complaint_store
    if store is None:
        return AnalyticsSummary(
            total_complaints=0,
            by_department={},
            by_urgency={"low": 0, "medium": 0, "high": 0, "critical": 0},
            avg_urgency=0.0,
            active_clusters=[],
        )

    query = AnalyticsQuery(region=region, days=days, department=department)
    return store.get_analytics(query)

