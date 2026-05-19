# Contract: POST /api/v1/classify

**Version**: 1.0
**Module**: Auto-Routing API (single complaint)
**User Story**: US1 — Single Complaint Classification

## Request

**Method**: `POST`
**Path**: `/api/v1/classify`
**Content-Type**: `application/json`

### Request Body

```json
{
  "text": "pani nahi araha 4 din se G-9 mein",
  "language": "roman_urdu",
  "user_id": "user_123",
  "timestamp": "2026-05-20T10:30:00Z",
  "location_hint": null
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| text | string | ✅ | 3–5000 chars, non-empty |
| language | enum | ❌ | `roman_urdu` \| `urdu` \| `english` \| `mixed`. Auto-detected if omitted. |
| user_id | string | ❌ | ≤128 chars |
| timestamp | ISO 8601 | ❌ | Defaults to server time |
| location_hint | string | ❌ | Pre-extracted location from form field |

## Response — 200 OK

```json
{
  "schema_version": "1.0",
  "request_id": "req_abc123",
  "classification": {
    "department": "water_supply",
    "sub_category": "outage",
    "urgency_score": 0.78,
    "sentiment": "negative",
    "confidence": 0.92,
    "urgency_keywords_matched": []
  },
  "location": {
    "raw_location": "G-9",
    "resolved_name": "G-9, Islamabad",
    "latitude": 33.7094,
    "longitude": 73.0348,
    "confidence": 0.95,
    "source": "gazetteer",
    "city": "Islamabad"
  },
  "cluster": {
    "cluster_id": "cluster_2026_05_water_001",
    "is_duplicate": true,
    "cluster_size": 12,
    "cluster_weight": 9.36,
    "similarity_score": 0.87
  },
  "suggested_response_urdu": "آپ کی شکایت درج کی جا چکی ہے۔ محکمہ آبپاشی کو بھیج دی گئی ہے۔",
  "processing_time_ms": 1850
}
```

## Response — 422 Validation Error

```json
{
  "schema_version": "1.0",
  "error_code": "VALIDATION_ERROR",
  "message": "Request body validation failed",
  "details": [
    {
      "field": "text",
      "message": "String should have at least 3 characters",
      "type": "string_too_short"
    }
  ]
}
```

## Response — 503 Service Degraded

Returned when all ML providers are unavailable and keyword fallback is used.

```json
{
  "schema_version": "1.0",
  "request_id": "req_abc124",
  "classification": {
    "department": "water_supply",
    "sub_category": "general",
    "urgency_score": 0.5,
    "sentiment": "neutral",
    "confidence": 0.3,
    "urgency_keywords_matched": ["pani"]
  },
  "location": null,
  "cluster": null,
  "suggested_response_urdu": "آپ کی شکایت موصول ہو گئی ہے۔",
  "processing_time_ms": 50,
  "_warnings": [
    "LLM providers unavailable — using keyword-only fallback with reduced accuracy"
  ]
}
```
