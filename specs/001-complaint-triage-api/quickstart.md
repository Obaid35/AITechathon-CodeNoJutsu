# Quickstart: NaqsKAR API

**Time to first API call**: ~5 minutes

## Prerequisites

- Python 3.11+
- Claude API key (get one at https://console.anthropic.com)
- Optionally: Ollama installed locally for fallback

## 1. Clone & Setup

```bash
git clone https://github.com/Obaid35/AITechathon-CodeNoJutsu.git
cd AITechathon-CodeNoJutsu
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional — defaults shown
APP_LLM_PROVIDER=claude
APP_NORMALIZER_STRATEGY=llm
APP_CLASSIFIER_STRATEGY=llm
APP_GEO_STRATEGY=llm_gazetteer
APP_DEDUP_STRATEGY=embedding
HOST=0.0.0.0
PORT=8000
DEBUG=true
DEDUP_WINDOW_DAYS=7
DEDUP_RADIUS_METERS=500
```

## 3. Start the Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     NaqsKAR pipeline initialized: normalizer=llm, classifier=llm, geo=llm_gazetteer, dedup=embedding
```

## 4. Verify Health

```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

## 5. Classify Your First Complaint

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "pani nahi araha 4 din se G-9 mein",
    "language": "roman_urdu"
  }'
```

Expected response:

```json
{
  "schema_version": "1.0",
  "classification": {
    "department": "water_supply",
    "sub_category": "outage",
    "urgency_score": 0.78,
    "sentiment": "negative"
  },
  "location": {
    "resolved_name": "G-9, Islamabad",
    "latitude": 33.7094,
    "longitude": 73.0348
  },
  "suggested_response_urdu": "آپ کی شکایت درج کی جا چکی ہے۔"
}
```

## 6. Try More Examples

**Urdu script**:
```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "بجلی کا بل غلط ہے اسلام آباد سیکٹر F-7"}'
```

**High-urgency (English)**:
```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Child injured, need ambulance near Jinnah Hospital Lahore"}'
```

**Batch**:
```bash
curl -X POST http://localhost:8000/api/v1/batch-classify \
  -H "Content-Type: application/json" \
  -d '{
    "complaints": [
      {"text": "pani nahi araha G-9 mein"},
      {"text": "bijli nahi hai I-8 sector"},
      {"text": "road pe pothole hai F-10 markaz"}
    ]
  }'
```

## 7. View API Docs

Open in browser: http://localhost:8000/docs

## 8. Demo Each Module Independently

```bash
# Normalizer standalone demo
python -m app.modules.normalizer

# Classifier standalone demo
python -m app.modules.classifier

# Geo-Extractor standalone demo
python -m app.modules.geo_extractor

# Deduplication standalone demo
python -m app.modules.deduplication
```

## 9. Open the Dashboard

Open `dashboard/index.html` in your browser, or serve it:

```bash
python -m http.server 3000 --directory dashboard
```

Then visit http://localhost:3000 — the heatmap will load complaint clusters from the API.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ANTHROPIC_API_KEY not set` | Add your key to `.env` |
| Claude API timeout | Set `APP_LLM_PROVIDER=ollama` and ensure Ollama is running |
| sentence-transformers OOM | Set `APP_DEDUP_STRATEGY=none` to disable deduplication |
| Port 8000 in use | Change `PORT` in `.env` or use `--port 8001` |
