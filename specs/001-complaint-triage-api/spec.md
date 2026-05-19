# Feature Specification: NaqsKAR — AI Complaint Triage & Routing API

**Feature Branch**: `001-complaint-triage-api`
**Created**: 2026-05-20
**Status**: Draft
**Input**: User description: "AI-Powered Citizen Complaint Triage & Routing for Pakistan's E-Governance — full proposal from Gamma Developers for FYS 2026 AI Techathon"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Single Complaint Classification (Priority: P1) 🎯 MVP

A citizen submits a complaint in Roman Urdu, Urdu script, or English through any intake channel. NaqsKAR receives the raw text, normalizes it into a structured intent, classifies it by department and urgency, extracts location information, and returns a fully structured JSON response that a government ticketing system can consume directly.

**Why this priority**: This is the core value proposition — the end-to-end pipeline from raw multilingual text to actionable intelligence. Without this, nothing else matters.

**Independent Test**: Submit a Roman Urdu complaint string to the `/api/v1/classify` endpoint and verify the response contains valid department, urgency score, location, and suggested Urdu response template.

**Acceptance Scenarios**:

1. **Given** a Roman Urdu complaint "pani nahi araha 4 din se G-9 mein", **When** submitted to the classify endpoint, **Then** the response contains `department: water_supply`, an urgency score between 0.6–1.0, location entity "G-9" resolved to Islamabad coordinates, and a suggested Urdu response template.
2. **Given** an Urdu script complaint "بجلی کا بل غلط ہے اسلام آباد سیکٹر F-7", **When** submitted to the classify endpoint, **Then** the response contains `department: electricity`, location "F-7, Islamabad", and a sentiment classification.
3. **Given** an English complaint "Pothole on Constitution Avenue near Marriott", **When** submitted to the classify endpoint, **Then** the response contains `department: roads`, location resolved from "Constitution Avenue" and "Marriott" landmarks.
4. **Given** a complaint with high-urgency keywords like "baccha", "hospital", "khoon", or "aag", **When** classified, **Then** the urgency score MUST be ≥ 0.8 regardless of department.
5. **Given** an empty or gibberish complaint text, **When** submitted, **Then** the system returns a structured error with `422` status and field-level validation messages.

---

### User Story 2 — Batch Complaint Processing (Priority: P2)

A government operator needs to process a backlog of complaints received overnight. They submit a batch of complaint texts (up to 100 per request) and receive structured classifications for all of them in a single API call, enabling bulk triage without one-by-one processing.

**Why this priority**: Batch processing is critical for integration with government backends that accumulate complaints in queues. Enables overnight and bulk-processing workflows.

**Independent Test**: Submit an array of 5+ complaints in mixed languages to the batch endpoint and verify each returns a complete classification result.

**Acceptance Scenarios**:

1. **Given** a batch of 10 complaints in mixed languages, **When** submitted to the batch-classify endpoint, **Then** the response contains 10 individual classification results, each with department, urgency, location, and sentiment.
2. **Given** a batch exceeding the maximum allowed size, **When** submitted, **Then** the system returns a clear error indicating the limit and current count.
3. **Given** a batch where 2 out of 5 complaints are malformed, **When** submitted, **Then** the system returns results for the 3 valid complaints and structured per-item errors for the 2 invalid ones — it does NOT fail the entire batch.

---

### User Story 3 — Semantic Deduplication & Clustering (Priority: P3)

When multiple citizens report the same issue (e.g., 50 people reporting a broken water main in G-9), NaqsKAR detects that these complaints are semantically similar, geographically proximate, and temporally close. It clusters them into a single high-priority issue with a computed severity weight, preventing ticket chaos in the backend system.

**Why this priority**: Deduplication transforms raw complaint volume into actionable intelligence. However, it depends on classification and geo-extraction working first, making it P3.

**Independent Test**: Submit 5+ semantically similar complaints with nearby locations and verify they are assigned to the same cluster with an escalated severity weight.

**Acceptance Scenarios**:

1. **Given** 5 complaints about water outage within 500m of each other submitted within 7 days, **When** processed, **Then** all 5 are assigned the same `cluster_id` and the cluster weight reflects `count × average urgency`.
2. **Given** 2 complaints about different issues at the same location, **When** processed, **Then** they are assigned to different clusters.
3. **Given** 2 semantically similar complaints more than 500m apart, **When** processed, **Then** they are placed in separate clusters.

---

### User Story 4 — Analytics & Heatmap Data (Priority: P4)

Decision-makers (bureaucrats, district commissioners) query NaqsKAR for aggregated analytics data: complaint volume by region, department breakdown, trending issues, and geographic heatmap coordinates. This data powers both internal dashboards and the public transparency heatmap.

**Why this priority**: Analytics is a value-add layer built on top of classified and clustered data. It requires all upstream modules to be functional first.

**Independent Test**: Query the analytics endpoint with a region filter and verify it returns complaint counts by department, urgency distribution, and geographic cluster coordinates.

**Acceptance Scenarios**:

1. **Given** at least 10 classified complaints for Islamabad in the last 7 days, **When** the analytics endpoint is queried with `region=Islamabad&days=7`, **Then** the response contains department-wise complaint counts, average urgency per department, and a list of geographic clusters with coordinates.
2. **Given** no complaints matching the query filter, **When** queried, **Then** the system returns an empty result set with zero counts — not an error.

---

### User Story 5 — Public Heatmap Dashboard (Priority: P5)

Citizens and media access a live, filterable map showing clustered complaint issues by district and category. The dashboard provides transparency into government responsiveness and highlights geographic patterns of infrastructure failure.

**Why this priority**: The dashboard is the public-facing showcase but depends on all backend modules (classification, geo, clustering, analytics) being operational. It is the final layer.

**Independent Test**: Load the dashboard URL, verify the map renders with complaint clusters, and confirm that filtering by department and date range updates the displayed data.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded, **When** complaint data exists, **Then** the map displays colored markers/clusters with count badges at the correct geographic positions.
2. **Given** a department filter is applied, **When** the user selects "water_supply", **Then** only water-related complaint clusters are shown on the map.
3. **Given** a date range is selected, **When** the user narrows to "last 3 days", **Then** only complaints within that window appear.

---

### Edge Cases

- What happens when a complaint is in a language or script not supported (e.g., Pashto, Sindhi)? The system MUST return a classification with a low confidence flag and fall back to English keyword matching.
- How does the system handle extremely short complaints (1–2 words)? It MUST attempt classification but flag the result as `low_confidence`.
- What happens if the LLM provider is unavailable? The system MUST fall back to the alternative provider or return a graceful degradation response.
- How does the system handle location mentions that don't exist in the gazetteer? It MUST attempt LLM-based fuzzy matching and return a `geo_confidence` score below 0.5 if uncertain.
- What happens when the embedding service is down for deduplication? Classification and routing MUST still work; deduplication returns `cluster_id: null` with a warning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept complaint text in Roman Urdu, Urdu script, and English and return structured classification output.
- **FR-002**: System MUST classify each complaint by department (from a configurable list of departments), sub-category, urgency score (0.0–1.0), and sentiment (positive / negative / neutral).
- **FR-003**: System MUST extract location entities from free-text and resolve them to latitude/longitude coordinates using a Pakistan-specific gazetteer.
- **FR-004**: System MUST support fuzzy/misspelled location matching with a confidence score.
- **FR-005**: System MUST detect high-urgency keywords (medical emergencies, fire, violence) and auto-elevate urgency score to ≥ 0.8.
- **FR-006**: System MUST embed complaints using sentence-level embeddings and cluster semantically similar complaints within a configurable time window (default 7 days) and geographic radius (default 500m).
- **FR-007**: System MUST expose a batch classification endpoint accepting up to 100 complaints per request with per-item error handling.
- **FR-008**: System MUST return a suggested response template in Urdu for each classified complaint.
- **FR-009**: System MUST provide a health check endpoint returning system status including model readiness.
- **FR-010**: System MUST provide an analytics endpoint returning complaint aggregates by region, department, urgency, and time range.
- **FR-011**: System MUST serve a public heatmap dashboard displaying clustered complaints on a geographic map with filtering by department and date range.
- **FR-012**: System MUST handle ML provider failures gracefully — classification and routing MUST still return results (possibly degraded) when the LLM or embedding service is unavailable.

### Key Entities

- **Complaint**: Raw text input with optional language hint, user ID, and timestamp. Core entity flowing through the entire pipeline.
- **Classification**: Department, sub-category, urgency score, sentiment, and confidence — the output of the classifier module.
- **Location**: Extracted geographic entity with resolved latitude/longitude, confidence score, and source (gazetteer match vs. LLM fallback).
- **Cluster**: A group of semantically similar, geographically proximate complaints within a time window. Has a computed severity weight and complaint count.
- **Department**: Configurable target routing destination (e.g., water_supply, electricity, roads, sanitation, police, health).
- **AnalyticsSummary**: Aggregated complaint metrics by region, department, time range — including cluster coordinates for heatmap rendering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A single complaint is classified and routed in under 3 seconds end-to-end, from API request to response.
- **SC-002**: Roman Urdu complaints receive equivalent classification accuracy to English complaints — measured by department-match accuracy on a 50-complaint gold set achieving ≥ 75% accuracy.
- **SC-003**: Location entities are correctly extracted and resolved for ≥ 80% of complaints that contain geographic references.
- **SC-004**: Semantically similar complaints about the same issue within 500m are clustered together with ≥ 70% precision.
- **SC-005**: The batch endpoint processes 100 complaints in under 60 seconds.
- **SC-006**: The system remains functional (single-complaint classification works) even when one ML provider is unavailable — verified by disabling the primary provider and confirming the fallback activates.
- **SC-007**: The heatmap dashboard loads and renders complaint clusters within 5 seconds on a standard broadband connection.
- **SC-008**: The system demonstrates the full end-to-end pipeline in a live demo: raw multilingual text input → structured classification → cluster assignment → heatmap visualization.

## Assumptions

- Target users include government complaint portal operators, utility company customer service teams, and public citizens viewing the transparency dashboard.
- The system will be deployed as a stateless API service; complaint persistence is handled by the integrating backend system, not by NaqsKAR itself (though NaqsKAR may use temporary in-memory or rolling-window storage for deduplication).
- Initial department taxonomy covers 8–12 major Pakistani government departments (water, electricity, roads, sanitation, police, health, education, revenue, telecom, gas). The list is configurable.
- The Pakistan gazetteer covers major cities, sectors (Islamabad), tehsils, and well-known landmarks. Coverage gaps are handled by LLM fallback.
- Mobile support for the dashboard is out of scope for v1; desktop browser is the target.
- Authentication and API key management are out of scope for the hackathon MVP but the architecture accommodates adding them later.
- Training data is bootstrapped from synthetic LLM-generated examples and a team-labeled gold set of ~300 complaints. No access to real PCP data is assumed.
