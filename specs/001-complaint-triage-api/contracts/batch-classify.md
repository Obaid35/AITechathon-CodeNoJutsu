# Contract: POST /api/v1/batch-classify

**Version**: 1.0
**Module**: Auto-Routing API (batch processing)
**User Story**: US2 — Batch Complaint Processing

## Request

**Method**: `POST`
**Path**: `/api/v1/batch-classify`
**Content-Type**: `application/json`

### Request Body

```json
{
  "complaints": [
    {
      "text": "pani nahi araha 4 din se G-9 mein",
      "language": "roman_urdu",
      "user_id": "user_123"
    },
    {
      "text": "سڑک ٹوٹی ہے F-7 میں",
      "language": "urdu"
    },
    {
      "text": "Electricity bill is incorrect for house in I-8",
      "language": "english"
    }
  ]
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| complaints | array[Complaint] | ✅ | 1–100 items. Each item follows the same schema as the single classify request body. |

## Response — 200 OK

Per-item results with partial failure support. Individual items that fail validation get inline errors instead of classifications.

```json
{
  "schema_version": "1.0",
  "request_id": "req_batch_456",
  "total": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "index": 0,
      "status": "success",
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
      "cluster": null,
      "suggested_response_urdu": "آپ کی شکایت درج کی جا چکی ہے۔"
    },
    {
      "index": 1,
      "status": "error",
      "error": {
        "error_code": "VALIDATION_ERROR",
        "message": "Complaint text too short",
        "details": [{"field": "text", "message": "String should have at least 3 characters"}]
      }
    },
    {
      "index": 2,
      "status": "success",
      "classification": {
        "department": "electricity",
        "sub_category": "billing",
        "urgency_score": 0.45,
        "sentiment": "negative",
        "confidence": 0.88,
        "urgency_keywords_matched": []
      },
      "location": {
        "raw_location": "I-8",
        "resolved_name": "I-8, Islamabad",
        "latitude": 33.6844,
        "longitude": 73.0479,
        "confidence": 0.97,
        "source": "gazetteer",
        "city": "Islamabad"
      },
      "cluster": null,
      "suggested_response_urdu": "آپ کی شکایت موصول ہو گئی ہے۔"
    }
  ],
  "processing_time_ms": 5200
}
```

## Response — 422 Validation Error

Returned when the batch-level request is invalid (e.g., empty array, >100 items).

```json
{
  "schema_version": "1.0",
  "error_code": "VALIDATION_ERROR",
  "message": "Batch size must be between 1 and 100",
  "details": [
    {
      "field": "complaints",
      "message": "List should have at most 100 items, got 150",
      "type": "too_long"
    }
  ]
}
```
