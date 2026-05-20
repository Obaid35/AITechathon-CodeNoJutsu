"""Analytics schemas for the analytics endpoint."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsQuery(BaseModel):
    """Query parameters for the analytics endpoint."""

    region: str = Field("all", description="City or region filter")
    days: int = Field(7, ge=1, le=90, description="Time window in days")
    department: str = Field("all", description="Department filter")


class ClusterSummary(BaseModel):
    """Cluster summary for heatmap rendering."""

    cluster_id: str
    department: str
    complaint_count: int
    avg_urgency: float = 0.0
    weight: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    representative_text: str


class AnalyticsSummary(BaseModel):
    """Aggregated analytics response."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "1.0",
                    "request_id": "req_analytics_789",
                    "region": "Islamabad",
                    "period_days": 7,
                    "total_complaints": 156,
                    "by_department": {"water_supply": 42, "electricity": 38},
                    "by_urgency": {
                        "critical": 14,
                        "high": 38,
                        "medium": 62,
                        "low": 42,
                    },
                    "avg_urgency": 0.54,
                    "clusters": [],
                    "generated_at": "2026-05-20T10:30:00Z",
                }
            ]
        }
    )

    schema_version: str = "1.0"
    total_complaints: int
    by_department: dict[str, int]
    by_urgency: dict[str, int]
    avg_urgency: float
    active_clusters: list[ClusterSummary] = []
    generated_at: Optional[datetime] = None
