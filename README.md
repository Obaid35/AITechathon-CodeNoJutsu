# NaqsKAR
**AI-Powered Citizen Complaint Triage & Routing for Pakistan**

Built by **Code no Jutsu** (Gamma Developers) for the FYS 2026 AI Techathon.

NaqsKAR is an AI/ML SaaS layer that sits between citizen complaint intake channels (web forms, WhatsApp, IVR) and government ticketing backends. It understands complaints written in Roman Urdu, Urdu, and English, classifies them, extracts location entities, deduplicates mass-reported issues, and routes them.

## Alignment with 5 Es Framework
- **Primary (E-Pakistan):** Core infrastructure for e-governance. Enables ICT services and technology-enabled service delivery at scale.
- **Secondary (Equity & Empowerment):** Levels the playing field for non-English speakers. A casual Roman Urdu complaint gets the same AI-powered triage quality as a formal English one.

## Architecture

1. **Multilingual Normalizer**: Groq Llama 3.1 handles translation and normalization of code-mixed Roman Urdu.
2. **Multi-Label Classifier**: (Zero-Shot Transformer / LLM) Predicts department, sub-category, urgency, and sentiment.
3. **Geo-Extractor**: Custom Pakistan gazetteer + RapidFuzz to resolve free-text locations to coordinates.
4. **Semantic Deduplicator**: Local `sentence-transformers` (`MiniLM-L12`) calculates cosine similarity and clusters duplicates within a 7-day/0.5km window.
5. **Database**: Supabase `pgvector` for persistence and vector similarity search.
6. **Dashboard**: Next.js + Tailwind React application with split Citizen/Bureaucrat views.

## Setup & Run Instructions

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Environment Variables** (`backend/.env`):
```ini
GROQ_API_KEY=your_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

**Database Setup**:
Run the SQL from `backend/data/schema.sql` in your Supabase SQL Editor.

**Start the API**:
```bash
python -m app.main
```
(Runs on http://localhost:8000)

### 2. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
(Runs on http://localhost:3000)

### 3. Demo Roles
- **Citizen**: Go to the dashboard, submit a complaint, view the Heatmap.
- **Bureaucrat**: Click "Bureaucrat Login" in the header (Creds: `admin` / `pakistan`). This unlocks the Analytics tab and the ability to resolve complaints in the Live Feed.

### Evaluation
To run the evaluation script for the judges (demonstrating model accuracy):
```bash
cd backend
set PYTHONPATH=.
python scripts/evaluate.py
```
