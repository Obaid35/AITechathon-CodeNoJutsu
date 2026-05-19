"""Request schemas for complaint classification.

Constitution IV: Pydantic v2 models with json_schema_extra examples.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LanguageEnum(str, Enum):
    ROMAN_URDU = "roman_urdu"
    URDU = "urdu"
    ENGLISH = "english"
    MIXED = "mixed"


class ClassifyRequest(BaseModel):
    """Single complaint classification request."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "pani nahi araha 4 din se G-9 mein",
                    "language": "roman_urdu",
                    "user_id": "user_123",
                }
            ]
        }
    )

    text: str = Field(
        ..., min_length=3, max_length=5000, description="Raw complaint text"
    )
    language: Optional[LanguageEnum] = Field(
        None, description="Language hint. Auto-detected if omitted."
    )
    user_id: Optional[str] = Field(
        None, max_length=128, description="Caller/citizen identifier"
    )
    timestamp: Optional[datetime] = Field(
        None, description="When the complaint was filed. Defaults to server time."
    )
    location_hint: Optional[str] = Field(
        None, description="Pre-extracted location from form field"
    )


class BatchClassifyRequest(BaseModel):
    """Batch complaint classification request."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "complaints": [
                        {"text": "pani nahi araha G-9 mein", "language": "roman_urdu"},
                        {"text": "bijli nahi hai I-8 sector"},
                    ]
                }
            ]
        }
    )

    complaints: list[ClassifyRequest] = Field(
        ..., min_length=1, max_length=100, description="List of complaints (1-100)"
    )
