"""Cluster info schema for semantic deduplication module."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClusterInfo(BaseModel):
    """Cluster assignment for a complaint."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "cluster_id": "cluster_2026_05_water_001",
                    "is_duplicate": True,
                    "cluster_size": 12,
                    "cluster_weight": 9.36,
                    "similarity_score": 0.87,
                }
            ]
        }
    )

    cluster_id: Optional[str] = Field(None, description="Cluster identifier")
    is_duplicate: bool = Field(
        ..., description="Whether this complaint matched an existing cluster"
    )
    cluster_size: Optional[int] = Field(None, description="Complaints in cluster")
    cluster_weight: Optional[float] = Field(
        None, description="Severity weight: count × avg_urgency"
    )
    similarity_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Cosine similarity to centroid"
    )
