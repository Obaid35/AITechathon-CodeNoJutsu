"""Classification result and response schemas.

Constitution IV: schema_version on all responses, typed models at boundaries.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cluster import ClusterInfo
from app.schemas.location import LocationResult


class SentimentEnum(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ClassificationResult(BaseModel):
    """Output of the classifier module."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "department": "water_supply",
                    "sub_category": "outage",
                    "urgency_score": 0.78,
                    "sentiment": "negative",
                    "confidence": 0.92,
                    "urgency_keywords_matched": [],
                }
            ]
        }
    )

    department: str = Field(..., description="Target department ID")
    sub_category: str = Field(..., description="Sub-category within department")
    urgency_score: float = Field(
        ..., ge=0.0, le=1.0, description="Urgency on 0-1 scale"
    )
    sentiment: SentimentEnum = Field(..., description="Sentiment classification")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Classification confidence"
    )
    urgency_keywords_matched: list[str] = Field(
        default_factory=list, description="Matched urgency keywords"
    )


class ClassifyResponse(BaseModel):
    """Full response for single complaint classification."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "1.0",
                    "request_id": "req_abc123",
                    "classification": {
                        "department": "water_supply",
                        "sub_category": "outage",
                        "urgency_score": 0.78,
                        "sentiment": "negative",
                        "confidence": 0.92,
                        "urgency_keywords_matched": [],
                    },
                    "location": {
                        "raw_location": "G-9",
                        "resolved_name": "G-9, Islamabad",
                        "latitude": 33.7094,
                        "longitude": 73.0348,
                        "confidence": 0.95,
                        "source": "gazetteer",
                        "city": "Islamabad",
                    },
                    "cluster": None,
                    "suggested_response_urdu": "آپ کی شکایت درج کی جا چکی ہے۔",
                    "processing_time_ms": 1850,
                }
            ]
        }
    )

    schema_version: str = "1.0"
    request_id: str = Field(..., description="Unique request identifier")
    classification: ClassificationResult
    location: Optional[LocationResult] = None
    cluster: Optional[ClusterInfo] = None
    suggested_response_urdu: str = Field(
        ..., description="Auto-generated Urdu response template"
    )
    processing_time_ms: int = Field(
        ..., description="End-to-end processing time in milliseconds"
    )
    _warnings: Optional[list[str]] = Field(
        default=None, description="Degradation warnings"
    )


# --- Batch response models ---


class BatchItemResult(BaseModel):
    """Result for a single item in a batch request."""

    index: int
    status: str = Field(..., description="'success' or 'error'")
    classification: Optional[ClassificationResult] = None
    location: Optional[LocationResult] = None
    cluster: Optional[ClusterInfo] = None
    suggested_response_urdu: Optional[str] = None
    error: Optional[dict] = None


class BatchClassifyResponse(BaseModel):
    """Full response for batch complaint classification."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "1.0",
                    "request_id": "req_batch_456",
                    "total": 3,
                    "successful": 2,
                    "failed": 1,
                    "results": [],
                    "processing_time_ms": 5200,
                }
            ]
        }
    )

    schema_version: str = "1.0"
    request_id: str
    total: int
    successful: int
    failed: int
    results: list[BatchItemResult]
    processing_time_ms: int
