# 🇵🇰 NaqsKAR — AI-Powered Citizen Complaint Triage & Routing

> **NaqsKAR** (نقشہ کار) = "Mapmaker" in Urdu — an AI system that maps citizen complaints to the right government department, instantly.

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776ab?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 What It Does

NaqsKAR accepts citizen complaints in **Roman Urdu**, **Urdu script**, or **English** and automatically:

1. **🧠 Classifies** → Routes to the correct department (water, electricity, roads, health, etc.)
2. **📍 Geo-locates** → Resolves location references to coordinates via a 38-entry Pakistan gazetteer
3. **🔁 Deduplicates** → Clusters similar complaints using multilingual sentence embeddings
4. **📊 Prioritizes** → Urgency scoring (0-1) with keyword boosting for emergency terms
5. **🗺️ Visualizes** → Live heatmap dashboard with Leaflet.js

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI Server                     │
│                                                       │
│  POST /api/v1/classify                                │
│       ↓                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Normalizer   │  │ Geo-Extractor│  │ Deduplicator │ │
│  │ (LLM via     │  │ (Gazetteer + │  │ (Sentence    │ │
│  │  OpenRouter)  │  │  LLM)        │  │  Transformers│ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         ↓                  ↓                  ↓        │
│  ┌─────────────┐                                      │
│  │ Classifier   │ → ClassifyResponse                  │
│  │ (LLM +       │ → AnalyticsStore                    │
│  │  Keywords)    │ → Dashboard                        │
│  └──────────────┘                                     │
│                                                       │
│  GET /api/v1/analytics → Aggregated data              │
│  GET /dashboard        → Live heatmap                 │
└─────────────────────────────────────────────────────┘
```

**Key Design Principles:**
- **Protocol-based modules** — Each module implements a swappable Protocol (ABC)
- **Parallel execution** — Normalizer + Geo run via `asyncio.gather()`
- **Graceful degradation** — LLM failures fall back to keyword matching
- **Structured logging** — Every request gets a `request_id` for tracing

---

## 🚀 Quickstart

### 1. Clone & Install

```bash
git clone https://github.com/Obaid35/AITechathon-CodeNoJutsu.git
cd AITechathon-CodeNoJutsu

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key:
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 3. Run

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Test

```bash
# Single complaint
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "pani nahi araha 4 din se G-9 mein", "language": "roman_urdu"}'

# Seed demo data (20 complaints)
python scripts/seed_demo.py

# Open dashboard
# http://localhost:8000/dashboard
```

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/classify` | Classify a single complaint |
| `POST` | `/api/v1/batch-classify` | Batch classify (up to 100) |
| `GET` | `/api/v1/analytics` | Aggregated analytics data |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/dashboard` | Live heatmap dashboard |

### Example Response

```json
{
  "classification": {
    "department": "water_supply",
    "sub_category": "outage",
    "urgency_score": 0.78,
    "sentiment": "negative",
    "confidence": 0.95
  },
  "location": {
    "resolved_name": "G-9, Islamabad",
    "latitude": 33.7094,
    "longitude": 73.0348,
    "source": "gazetteer"
  },
  "cluster": {
    "cluster_id": "cluster_abc123",
    "is_duplicate": true,
    "cluster_size": 4,
    "cluster_weight": 3.12
  },
  "suggested_response_urdu": "آپ کی شکایت درج کی جا چکی ہے۔ محکمہ آبپاشی کو بھیج دی گئی ہے۔"
}
```

---

## 🗺️ Dashboard

The heatmap dashboard at `/dashboard` shows:
- **Cluster markers** color-coded by department, sized by complaint count
- **Real-time stats** — total complaints, critical/high counts, avg urgency
- **Filters** — by department, region, and time window
- **Test panel** — submit complaints directly from the dashboard
- Auto-refreshes every 30 seconds

---

## 🐳 Docker

```bash
docker-compose up --build
# API: http://localhost:8000
# Dashboard: http://localhost:8000/dashboard
```

---

## 📁 Project Structure

```
├── app/
│   ├── api/v1/          # FastAPI routes
│   ├── core/            # Config, errors, logging
│   ├── data/            # Gazetteer, templates, samples
│   ├── modules/
│   │   ├── normalizer/  # Text normalization + LLM
│   │   ├── classifier/  # Department classification
│   │   ├── geo_extractor/ # Location resolution
│   │   └── deduplication/ # Semantic clustering
│   ├── orchestrator/    # Pipeline + complaint store
│   ├── schemas/         # Pydantic models
│   └── main.py          # FastAPI app entry point
├── dashboard/           # Leaflet.js heatmap UI
├── scripts/             # Seed & test scripts
├── specs/               # Feature specifications
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🤖 LLM Configuration

NaqsKAR uses **OpenRouter** with the free **GLM-4.5-Air** model by default:

| Setting | Default | Description |
|---------|---------|-------------|
| `OPENROUTER_API_KEY` | (required) | Your OpenRouter API key |
| `OPENROUTER_MODEL` | `z-ai/glm-4.5-air:free` | Model to use |
| `APP_DEDUP_STRATEGY` | `embedding` | `embedding` or `none` |
| `DEDUP_WINDOW_DAYS` | `7` | Cluster time window |
| `DEDUP_RADIUS_METERS` | `500` | Geographic proximity |

---

## 👥 Team: Code No Jutsu

Built for **AI Techathon 2026** 🇵🇰

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
