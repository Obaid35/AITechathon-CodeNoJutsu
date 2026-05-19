"""Location result schema for geo-extraction module."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GeoSourceEnum(str, Enum):
    GAZETTEER = "gazetteer"
    LLM_FALLBACK = "llm_fallback"
    NONE = "none"


class LocationResult(BaseModel):
    """Resolved geographic location from complaint text."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "raw_location": "G-9",
                    "resolved_name": "G-9, Islamabad",
                    "latitude": 33.7094,
                    "longitude": 73.0348,
                    "confidence": 0.95,
                    "source": "gazetteer",
                    "city": "Islamabad",
                }
            ]
        }
    )

    raw_location: str = Field(..., description="Location entity as extracted from text")
    resolved_name: str = Field(..., description="Canonical location name")
    latitude: Optional[float] = Field(None, description="Resolved latitude")
    longitude: Optional[float] = Field(None, description="Resolved longitude")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Geo-resolution confidence"
    )
    source: GeoSourceEnum = Field(..., description="Resolution source")
    city: Optional[str] = Field(None, description="City name if resolved")
