"""In-memory complaint store for analytics aggregation.

Stores processed ClassifyResponse entries for querying and analytics.
Constitution III: Thread-safe in-memory store.
"""

import time
from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger
from app.schemas.analytics import AnalyticsQuery, AnalyticsSummary, ClusterSummary
from app.schemas.classification import ClassifyResponse

logger = get_logger("analytics.store")


class InMemoryComplaintStore:
    """Stores processed complaints for analytics queries."""

    def __init__(self) -> None:
        self._complaints: list[dict] = []

    def add(self, response: ClassifyResponse) -> None:
        """Store a processed complaint response."""
        entry = {
            "request_id": response.request_id,
            "department": response.classification.department,
            "sub_category": response.classification.sub_category,
            "urgency_score": response.classification.urgency_score,
            "sentiment": response.classification.sentiment.value,
            "confidence": response.classification.confidence,
            "location": None,
            "cluster_id": None,
            "cluster_size": None,
            "timestamp": time.time(),
            "suggested_response_urdu": response.suggested_response_urdu,
        }

        if response.location:
            entry["location"] = {
                "raw": response.location.raw_location,
                "resolved": response.location.resolved_name,
                "lat": response.location.latitude,
                "lon": response.location.longitude,
                "city": response.location.city,
            }

        if response.cluster:
            entry["cluster_id"] = response.cluster.cluster_id
            entry["cluster_size"] = response.cluster.cluster_size

        self._complaints.append(entry)
        logger.info(
            "complaint_stored",
            request_id=response.request_id,
            department=response.classification.department,
            total_stored=len(self._complaints),
        )

    def query(
        self,
        region: Optional[str] = None,
        days: int = 7,
        department: Optional[str] = None,
    ) -> list[dict]:
        """Query stored complaints with filters."""
        cutoff = time.time() - (days * 86400)
        results = []

        for c in self._complaints:
            # Time filter
            if c["timestamp"] < cutoff:
                continue

            # Region filter
            if region and region != "all":
                loc = c.get("location")
                if not loc or (loc.get("city", "").lower() != region.lower()):
                    continue

            # Department filter
            if department and department != "all":
                if c["department"] != department:
                    continue

            results.append(c)

        return results

    def get_analytics(self, query: AnalyticsQuery) -> AnalyticsSummary:
        """Compute aggregated analytics from stored complaints."""
        filtered = self.query(
            region=query.region,
            days=query.days,
            department=query.department,
        )

        total = len(filtered)

        # By department
        by_department: dict[str, int] = {}
        for c in filtered:
            dept = c["department"]
            by_department[dept] = by_department.get(dept, 0) + 1

        # By urgency band
        by_urgency = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        urgency_sum = 0.0
        for c in filtered:
            u = c["urgency_score"]
            urgency_sum += u
            if u <= 0.3:
                by_urgency["low"] += 1
            elif u <= 0.6:
                by_urgency["medium"] += 1
            elif u <= 0.8:
                by_urgency["high"] += 1
            else:
                by_urgency["critical"] += 1

        avg_urgency = round(urgency_sum / total, 3) if total > 0 else 0.0

        # Active clusters with coordinates
        cluster_map: dict[str, dict] = {}
        for c in filtered:
            cid = c.get("cluster_id")
            if not cid:
                continue
            if cid not in cluster_map:
                cluster_map[cid] = {
                    "cluster_id": cid,
                    "complaint_count": 0,
                    "department": c["department"],
                    "avg_urgency": 0.0,
                    "urgency_sum": 0.0,
                    "representative_text": c.get("suggested_response_urdu", ""),
                    "latitude": None,
                    "longitude": None,
                }
            cluster_map[cid]["complaint_count"] += 1
            cluster_map[cid]["urgency_sum"] += c["urgency_score"]

            # Use first available location
            loc = c.get("location")
            if loc and cluster_map[cid]["latitude"] is None:
                cluster_map[cid]["latitude"] = loc.get("lat")
                cluster_map[cid]["longitude"] = loc.get("lon")

        clusters = []
        for cid, data in cluster_map.items():
            count = data["complaint_count"]
            avg_u = round(data["urgency_sum"] / count, 3) if count > 0 else 0.0
            clusters.append(
                ClusterSummary(
                    cluster_id=cid,
                    complaint_count=count,
                    department=data["department"],
                    avg_urgency=avg_u,
                    weight=round(count * avg_u, 2),
                    representative_text=data["representative_text"],
                    latitude=data["latitude"],
                    longitude=data["longitude"],
                )
            )

        return AnalyticsSummary(
            total_complaints=total,
            by_department=by_department,
            by_urgency=by_urgency,
            avg_urgency=avg_urgency,
            active_clusters=clusters,
        )
