"""Complaint processing pipeline — orchestrates all modules.

Constitution I: End-to-end pipeline from raw text to structured response.
Constitution II: Modules communicate only through this orchestrator.
Constitution III: Uses asyncio.gather() for parallel module execution.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger
from app.modules.classifier.protocol import ClassifierProtocol
from app.modules.geo_extractor.protocol import GeoExtractorProtocol
from app.modules.normalizer.protocol import NormalizerProtocol
from app.schemas.classification import ClassifyResponse, ClassificationResult
from app.schemas.cluster import ClusterInfo
from app.schemas.complaint import ClassifyRequest
from app.schemas.location import LocationResult

logger = get_logger("orchestrator")


class ComplaintPipeline:
    """Wires normalizer → classifier → geo-extractor → (dedup) → response.

    Constitution II: Each module is invoked through its Protocol interface.
    Constitution III: Normalizer and geo-extractor run in parallel via gather().
    """

    def __init__(
        self,
        normalizer: NormalizerProtocol,
        classifier: ClassifierProtocol,
        geo_extractor: Optional[GeoExtractorProtocol],
        deduplicator=None,  # Added in Phase 5 (US3)
    ) -> None:
        self.normalizer = normalizer
        self.classifier = classifier
        self.geo_extractor = geo_extractor
        self.deduplicator = deduplicator
        self._response_templates = self._load_response_templates()

    def _load_response_templates(self) -> dict[str, str]:
        """Load Urdu response templates from JSON."""
        path = Path(__file__).resolve().parent.parent / "data" / "response_templates.json"
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("templates", {})
        except Exception as e:
            logger.warning("response_templates_load_failed", error=str(e))
            return {"default": "آپ کی شکایت موصول ہو گئی ہے۔"}

    def _get_response_template(self, department: str) -> str:
        """Get the Urdu response template for a department."""
        return self._response_templates.get(
            department, self._response_templates.get("default", "آپ کی شکایت موصول ہو گئی ہے۔")
        )

    async def process(self, request: ClassifyRequest, request_id: str) -> ClassifyResponse:
        """Process a single complaint through the full pipeline.

        Flow: normalize + geo (parallel) → classify → dedup → response
        """
        start = time.perf_counter()
        warnings: list[str] = []

        # Step 1: Normalize + Geo-extract IN PARALLEL (Constitution III)
        language_hint = request.language.value if request.language else None

        normalize_task = self.normalizer.process(request.text, language_hint)

        geo_result: Optional[LocationResult] = None
        if self.geo_extractor:
            geo_task = self.geo_extractor.extract(
                request.text, location_hint=request.location_hint
            )
            normalized, geo_result = await asyncio.gather(
                normalize_task, geo_task
            )
        else:
            normalized = await normalize_task

        logger.info(
            "pipeline_normalized",
            intent=normalized.extracted_intent,
            language=normalized.detected_language,
            confidence=normalized.confidence,
        )

        # Step 2: Classify based on normalized output
        classification = await self.classifier.classify(normalized)

        logger.info(
            "pipeline_classified",
            department=classification.department,
            urgency=classification.urgency_score,
            sentiment=classification.sentiment.value,
        )

        # Step 3: Deduplication (if available — wired in Phase 5)
        cluster: Optional[ClusterInfo] = None
        if self.deduplicator:
            try:
                cluster = await self.deduplicator.deduplicate(
                    request.text, classification, geo_result
                )
            except Exception as e:
                logger.warning("pipeline_dedup_failed", error=str(e))
                warnings.append(
                    "Deduplication unavailable — clustering disabled for this request"
                )

        # Step 4: Build response
        response_template = self._get_response_template(classification.department)
        duration_ms = round((time.perf_counter() - start) * 1000)

        return ClassifyResponse(
            request_id=request_id,
            classification=classification,
            location=geo_result,
            cluster=cluster,
            suggested_response_urdu=response_template,
            processing_time_ms=duration_ms,
            _warnings=warnings if warnings else None,
        )

    def get_module_status(self) -> dict[str, dict]:
        """Return status of all modules for health check."""
        status = {
            "normalizer": {
                "status": "ready",
                "strategy": type(self.normalizer).__name__,
            },
            "classifier": {
                "status": "ready",
                "strategy": type(self.classifier).__name__,
            },
            "geo_extractor": {
                "status": "ready" if self.geo_extractor else "disabled",
                "strategy": type(self.geo_extractor).__name__ if self.geo_extractor else "none",
            },
            "deduplication": {
                "status": "ready" if self.deduplicator else "not_initialized",
                "strategy": type(self.deduplicator).__name__ if self.deduplicator else "none",
            },
        }
        return status
