"""
NaqsKAR — Pydantic Models (Request/Response Schemas)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Enums ──────────────────────────────────────────

class Department(str, Enum):
    WATER = "water_supply"
    ELECTRICITY = "electricity"
    GAS = "gas_supply"
    ROADS = "roads_infrastructure"
    SANITATION = "sanitation_sewerage"
    HEALTH = "health"
    EDUCATION = "education"
    POLICE = "police_security"
    FIRE = "fire_emergency"
    TRANSPORT = "public_transport"
    TELECOM = "telecom"
    REVENUE = "revenue_land"
    ENVIRONMENT = "environment"
    GENERAL = "general_complaint"


class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Sentiment(str, Enum):
    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"
    POLITE = "polite"


# ── Request Models ─────────────────────────────────

class ComplaintSubmit(BaseModel):
    """Raw complaint as received from citizen"""
    text: str = Field(..., min_length=5, max_length=2000, description="Complaint text in any language")
    source: str = Field(default="web", description="Intake channel: web, whatsapp, ivr")
    citizen_phone: Optional[str] = Field(default=None, description="Optional phone for follow-up")


# ── Response Models ────────────────────────────────

class GeoLocation(BaseModel):
    """Extracted and resolved location"""
    raw_text: str = Field(..., description="Location as extracted from complaint")
    resolved_name: str = Field(..., description="Standardized location name")
    latitude: float
    longitude: float
    confidence: float = Field(ge=0, le=1)


class ClassificationResult(BaseModel):
    """AI classification output"""
    department: Department
    sub_category: str
    urgency: UrgencyLevel
    urgency_score: float = Field(ge=0, le=1)
    sentiment: Sentiment
    keywords: list[str] = []


class ComplaintResponse(BaseModel):
    """Full structured response after processing"""
    id: str
    original_text: str
    normalized_text: str
    classification: ClassificationResult
    location: Optional[GeoLocation] = None
    cluster_id: Optional[str] = None
    cluster_size: Optional[int] = None
    source: str = "web"
    suggested_response_urdu: str
    processed_at: datetime


class ClusterResponse(BaseModel):
    """Deduplicated complaint cluster"""
    cluster_id: str
    representative_text: str
    department: Department
    urgency: UrgencyLevel
    location: Optional[GeoLocation] = None
    complaint_count: int
    weight: float
    complaint_ids: list[str]


class StatsResponse(BaseModel):
    """Dashboard analytics"""
    total_complaints: int
    by_department: dict[str, int]
    by_urgency: dict[str, int]
    avg_urgency_score: float
    top_locations: list[dict]
    clusters_active: int
