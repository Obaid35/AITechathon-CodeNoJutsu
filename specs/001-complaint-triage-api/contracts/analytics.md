# Contract: GET /api/v1/analytics

**Version**: 1.0
**Module**: Analytics API
**User Story**: US4 — Analytics & Heatmap Data

## Request

**Method**: `GET`
**Path**: `/api/v1/analytics`

### Query Parameters

| Parameter | Type | Required | Default | Constraints |
|-----------|------|----------|---------|-------------|
| region | string | ❌ | `all` | City or region name (e.g., `Islamabad`, `Lahore`). Case-insensitive. |
| days | integer | ❌ | `7` | Time window: 1–90 days. |
| department | string | ❌ | `all` | Filter by department ID (e.g., `water_supply`). |

### Example Request

```
GET /api/v1/analytics?region=Islamabad&days=7&department=all
```

## Response — 200 OK

```json
{
  "schema_version": "1.0",
  "request_id": "req_analytics_789",
  "region": "Islamabad",
  "period_days": 7,
  "total_complaints": 156,
  "by_department": {
    "water_supply": 42,
    "electricity": 38,
    "roads": 28,
    "sanitation": 22,
    "police": 12,
    "health": 8,
    "gas": 4,
    "education": 2
  },
  "by_urgency": {
    "critical": 14,
    "high": 38,
    "medium": 62,
    "low": 42
  },
  "avg_urgency": 0.54,
  "clusters": [
    {
      "cluster_id": "cluster_2026_05_water_001",
      "department": "water_supply",
      "complaint_count": 23,
      "weight": 17.94,
      "latitude": 33.7094,
      "longitude": 73.0348,
      "representative_text": "G-9 mein pani nahi araha kai dinon se"
    },
    {
      "cluster_id": "cluster_2026_05_elec_003",
      "department": "electricity",
      "complaint_count": 15,
      "weight": 12.0,
      "latitude": 33.7290,
      "longitude": 73.0550,
      "representative_text": "F-7 mein bijli 2 din se gul hai"
    }
  ],
  "generated_at": "2026-05-20T10:30:00Z"
}
```

## Response — 200 OK (Empty Result)

When no complaints match the filter, return zero counts — not an error.

```json
{
  "schema_version": "1.0",
  "request_id": "req_analytics_790",
  "region": "Quetta",
  "period_days": 7,
  "total_complaints": 0,
  "by_department": {},
  "by_urgency": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "avg_urgency": 0.0,
  "clusters": [],
  "generated_at": "2026-05-20T10:30:00Z"
}
```
