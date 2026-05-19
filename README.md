<!-- SEO Meta Tags -->
<!-- 
Description: NaqsKAR - AI-powered citizen complaint triage & routing for Pakistan's e-governance infrastructure. Multilingual NLP, smart classification, and automated routing.
Keywords: complaint triage, e-governance, Pakistan, NLP, multilingual AI, citizen engagement, E-Pakistan, Urdu NLP, complaint routing, SaaS
Author: Muhammad Zohaib Khan, Gamma Developers
Canonical: https://github.com/Obaid35/AITechathon-CodeNoJutsu
-->

<!-- Open Graph / Facebook -->
<!--
og:type: website
og:url: https://github.com/Obaid35/AITechathon-CodeNoJutsu
og:title: NaqsKAR - AI Complaint Triage for Pakistan's E-Governance
og:description: An intelligent SaaS layer that automates citizen complaint classification, urgency detection, and smart routing across Pakistan's government systems.
og:image: https://img.shields.io/badge/NaqsKAR-E%20Pakistan-2E7D32?style=for-the-badge
-->

<!-- Twitter Card -->
<!--
twitter:card: summary_large_image
twitter:url: https://github.com/Obaid35/AITechathon-CodeNoJutsu
twitter:title: NaqsKAR - AI-Powered Complaint Triage for Pakistan
twitter:description: Multilingual complaint routing system built for FYS 2026 AI Techathon
twitter:creator: @ZohaibCodez
-->

<!-- GitHub Metadata -->
<!--
topics: e-governance, NLP, complaint-management, Pakistan, multilingual-AI, Urdu, Roman-Urdu, government-tech, civic-engagement
languages: Python, JavaScript
-->

<div align="center">

# 🚀 NaqsKAR

### **AI-Powered Citizen Complaint Triage & Routing for Pakistan's E-Governance**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![FYS 2026](https://img.shields.io/badge/FYS%202026-AI%20Techathon-brightgreen?style=flat-square)](https://techathon.fys2026.com)
[![Hackathon](https://img.shields.io/badge/Status-In%20Development-orange?style=flat-square)](#)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab.svg?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)

**Aligns with:** E-Pakistan 🇵🇰 • Equity & Empowerment 👥

[📖 **About**](#about) • [✨ **Features**](#features) • [🚀 **Get Started**](#getting-started) • [📊 **Tech Stack**](#tech-stack) • [🗺️ **Roadmap**](#roadmap)

</div>

---

## 📋 Table of Contents

- [About](#about)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [API Endpoints](#api-endpoints)
  - [Example Requests](#example-requests)
- [Core Modules](#core-modules)
- [5 Es Framework Alignment](#5-es-framework-alignment)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Team](#team)

---

## 🎯 About

**NaqsKAR** is an AI/ML SaaS layer that sits between citizen complaint intake channels (web forms, WhatsApp, IVR) and government ticketing backends. It understands complaints written in **Roman Urdu, Urdu script, and English**, classifies them by department and urgency, extracts location entities, semantically deduplicates mass-reported issues, and routes them to the right authority — all via a clean, scalable API.

**Built for:** Pakistan Citizen Portal (PCP), provincial complaint systems, utility companies (KE, IESCO, SNGPL), and private complaint platforms (banks, telcos, e-commerce).

### Why NaqsKAR?

- 🌍 **Multilingual Intelligence**: 70%+ of Pakistani citizens lodge complaints in Roman Urdu or code-mixed text. NaqsKAR levels the playing field — a complaint in casual Roman Urdu gets the same triage quality as formal English.
- ⚡ **Smart Routing**: No more misdirected complaints. AI classifies by department, sub-category, and **urgency in real-time**.
- 📍 **Geographic Precision**: Extracts and resolves location entities (sector codes, landmarks, neighborhoods) using a custom Pakistan gazetteer + LLM fallback.
- 🔗 **Automatic Deduplication**: 200 citizens reporting the same broken transformer create ONE prioritized cluster, not 200 separate tickets.
- 📊 **Actionable Analytics**: Decision-makers get geographic and categorical heatmaps of infrastructure failures at scale.

---

## ⚠️ The Problem

Pakistan's public complaint infrastructure (PCP, PMDU, Awaz Punjab, KP Citizen Portal) receives **millions of grievances annually**. Despite massive citizen participation, the system suffers from critical inefficiencies:

| Challenge | Impact |
|-----------|--------|
| **Language Mismatch** | 70%+ of complaints arrive in Roman Urdu or code-mixed text; backend routing expects English keywords |
| **Misrouting** | Manual triage sends complaints to wrong departments (e.g., water leaks → roads department) |
| **No Deduplication** | Duplicate reports for same issue create ticket chaos instead of priority clustering |
| **No Urgency Detection** | Medical emergencies weighted the same as broken streetlights |
| **No Analytics** | Leaders lack visibility into where infrastructure is actually failing |

---

## 💡 The Solution

NaqsKAR is a **stateless, microservice-ready API** that ingests raw complaint text and outputs structured, actionable intelligence.

### Core Modules:

#### 1. **Multilingual Normalizer**
Fine-tuned multilingual transformer (XLM-R or mBERT-based) + few-shot LLM prompting that converts Roman Urdu, Urdu script, and code-mixed text into normalized intent + entities.

**Example:**
```
Input:  "pani nahi araha 4 din se G-9 mein"
Output: {
  "intent": "water_supply_outage",
  "duration": "4 days",
  "location": "G-9, Islamabad"
}
```

#### 2. **Multi-Label Classifier**
Predicts: (a) department, (b) sub-category, (c) urgency score (0–1), (d) sentiment.
Urgency is keyword-aware — terms like *baccha*, *hospital*, *khoon*, *aag* elevate priority automatically.

#### 3. **Geo-Extractor**
Pulls location entities (sector codes, neighborhood names, landmarks) from free-text and resolves them to lat/lon using a custom Pakistan gazetteer + LLM fallback for fuzzy/misspelled matches.

#### 4. **Semantic Deduplication**
Every complaint is embedded using sentence-transformers and clustered within a rolling 7-day window and 500m radius. Mass-reported issues collapse into single high-severity clusters with computed weight = (count × average urgency).

#### 5. **Auto-Routing API**
Returns structured JSON with department, sub-department, urgency, geo, cluster ID, and suggested response template in Urdu.

---

## ✨ Features

<table>
  <tr>
    <td>
      
**🌐 Multilingual NLP**
- Roman Urdu normalization
- Urdu script detection & parsing
- Code-mixed text handling
- Intent extraction

    </td>
    <td>
      
**🎯 Smart Classification**
- Multi-department routing
- Sub-category prediction
- Real-time urgency scoring
- Sentiment analysis

    </td>
  </tr>
  <tr>
    <td>
      
**📍 Geo Intelligence**
- Location entity extraction
- Pakistan gazetteer integration
- Fuzzy geo-matching with LLM
- Lat/lon resolution

    </td>
    <td>
      
**🔗 Deduplication & Analytics**
- Semantic similarity clustering
- Mass-issue detection
- 7-day rolling window deduplication
- Geographic heatmaps

    </td>
  </tr>
  <tr>
    <td colspan="2">
      
**⚙️ Enterprise Ready**
- RESTful API with JSON responses
- Stateless microservice architecture
- Scalable batch & streaming modes
- Ready for integration with PCP & provincial systems

    </td>
  </tr>
</table>

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Backend** | ![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi) |
| **NLP & ML** | ![Transformers](https://img.shields.io/badge/Hugging%20Face-Transformers-FDCC0D?style=flat-square) ![sentence-transformers](https://img.shields.io/badge/Sentence%20Transformers-Embeddings-4169E1?style=flat-square) ![scikit-learn](https://img.shields.io/badge/scikit--learn-Clustering-F7931E?style=flat-square) |
| **LLM** | ![Claude API](https://img.shields.io/badge/Claude%20API-LLM-8B5CF6?style=flat-square) ![Ollama](https://img.shields.io/badge/Ollama-Local%20LLMs-black?style=flat-square) |
| **Data Processing** | ![pandas](https://img.shields.io/badge/pandas-Data%20Wrangling-150458?style=flat-square) ![numpy](https://img.shields.io/badge/numpy-Computation-013243?style=flat-square) |
| **Frontend** | ![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react) ![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript) |
| **DevOps** | ![Docker](https://img.shields.io/badge/Docker-Containerization-2496ED?style=flat-square&logo=docker) ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088F0?style=flat-square&logo=github-actions) |

### Core Dependencies

```txt
fastapi==0.100.0          # High-performance web framework
transformers==4.30.0      # HuggingFace NLP models
sentence-transformers     # Semantic embeddings
pandas==2.0.0             # Data manipulation
scikit-learn==1.3.0       # Clustering & ML utilities
uvicorn==0.23.0           # ASGI server
python-dotenv             # Environment management
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLAINT INTAKE CHANNELS                       │
│   (Web Form, WhatsApp, IVR, Email, Social Media)           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    NAQSKAR API LAYER                         │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│ │  Multilingual│  │    Multi-    │  │     Geo-    │        │
│ │  Normalizer  │──│   Label      │──│  Extractor  │        │
│ │              │  │   Classifier │  │             │        │
│ └──────────────┘  └──────────────┘  └──────────────┘        │
│                           │                                  │
│                           ▼                                  │
│       ┌─────────────────────────────────┐                   │
│       │  Semantic Deduplication Engine  │                   │
│       │  (7-day rolling window, 500m)   │                   │
│       └─────────────────────────────────┘                   │
│                           │                                  │
│                           ▼                                  │
│       ┌─────────────────────────────────┐                   │
│       │   Auto-Routing Decision Engine  │                   │
│       │   (Department + Urgency + Geo)  │                   │
│       └─────────────────────────────────┘                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┬──────────────┐
         ▼                 ▼                 ▼              ▼
    ┌────────┐       ┌─────────┐       ┌─────────┐    ┌────────┐
    │   PCP  │       │ PMDU /  │       │Utility  │    │Private │
    │        │       │Provincial│      │Companies│    │Systems │
    └────────┘       └─────────┘       └─────────┘    └────────┘
```

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.9+** ([Download](https://www.python.org/downloads/))
- ✅ **Git** ([Download](https://git-scm.com/))
- ✅ **pip** or **poetry** (usually comes with Python)
- ✅ **Claude API Key** (optional, for LLM-powered features)

### Installation

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Obaid35/AITechathon-CodeNoJutsu.git
cd AITechathon-CodeNoJutsu
```

#### 2️⃣ Create a Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4️⃣ Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Claude API (optional for LLM features)
CLAUDE_API_KEY=your_api_key_here

# Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=False

# Model Configuration
MODEL_LANGUAGE=urdu  # or "en" or "mixed"
BATCH_SIZE=32
```

### Configuration

Create a `.env.example` file in the project root:

```bash
# NaqsKAR Configuration
CLAUDE_API_KEY=sk-ant-...
HOST=0.0.0.0
PORT=8000
WORKERS=4
DEBUG=True

# Model Paths
MULTILINGUAL_MODEL=xlm-roberta-base
EMBEDDING_MODEL=sentence-transformers/multilingual-e5-base
GAZETTEER_PATH=./data/pakistan_gazetteer.json

# Clustering
DEDUP_WINDOW_DAYS=7
DEDUP_RADIUS_METERS=500
```

---

## 📖 Usage

### Running the Server

```bash
# Development mode
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

Interactive API documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### API Endpoints

#### **POST** `/api/v1/classify`
Classify a single complaint.

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "pani nahi araha 4 din se G-9 mein",
    "language": "roman_urdu",
    "user_id": "user_123"
  }'
```

**Response:**
```json
{
  "classification": {
    "department": "water_supply",
    "sub_category": "outage",
    "urgency_score": 0.78,
    "sentiment": "negative"
  },
  "location": {
    "entity": "G-9",
    "latitude": 33.7490,
    "longitude": 73.1793,
    "confidence": 0.92
  },
  "cluster_id": "cluster_2024_05_water_001",
  "suggested_response_urdu": "آپ کی شکایت درج کی جا چکی ہے۔ ہم اس کو ترجیح سے حل کریں گے۔"
}
```

#### **POST** `/api/v1/batch-classify`
Classify multiple complaints at once.

```bash
curl -X POST http://localhost:8000/api/v1/batch-classify \
  -H "Content-Type: application/json" \
  -d '{
    "complaints": [
      {"text": "pani nahi araha", "language": "roman_urdu"},
      {"text": "سڑک ٹوٹی ہے", "language": "urdu"}
    ]
  }'
```

#### **GET** `/api/v1/analytics`
Get real-time analytics dashboard data.

```bash
curl http://localhost:8000/api/v1/analytics?days=7&region=Islamabad
```

---

### Example Requests

#### Multilingual Input Examples

```json
{
  "roman_urdu": "pani nahi araha 4 din se G-9 mein",
  "urdu_script": "بجلی کا بل غلط ہے اسلام آباد سیکٹر F-7",
  "english": "Pothole on Constitution Avenue near Marriott",
  "code_mixed": "road pe bohot badi hole h bilkul dangerous hai"
}
```

---

## 🔧 Core Modules

### Module 1: Multilingual Normalizer
**File:** `app/modules/multilingual_normalizer.py`

Converts raw user input into structured intent + entities.

```python
from app.modules import MultilingualNormalizer

normalizer = MultilingualNormalizer()
result = normalizer.process("pani nahi araha")
# Output: {"intent": "water_outage", "duration": "unknown", ...}
```

### Module 2: Multi-Label Classifier
**File:** `app/modules/classifier.py`

Predicts department, sub-category, urgency, and sentiment.

```python
from app.modules import MultiLabelClassifier

classifier = MultiLabelClassifier()
result = classifier.predict(normalized_text)
# Output: {"department": "water_supply", "urgency": 0.78, ...}
```

### Module 3: Geo-Extractor
**File:** `app/modules/geo_extractor.py`

Extracts and resolves location entities.

```python
from app.modules import GeoExtractor

extractor = GeoExtractor(gazetteer_path="data/pakistan_gazetteer.json")
result = extractor.extract("G-9 Islamabad")
# Output: {"location": "G-9, Islamabad", "lat": 33.749, "lon": 73.179}
```

### Module 4: Semantic Deduplication
**File:** `app/modules/deduplication.py`

Clusters similar complaints within time/space window.

```python
from app.modules import SemanticDeduplicator

deduplicator = SemanticDeduplicator(
    window_days=7,
    radius_meters=500
)
clusters = deduplicator.deduplicate(complaints_list)
```

### Module 5: Auto-Routing API
**File:** `app/api/routes.py`

Main FastAPI application with routing logic.

---

## 🌍 5 Es Framework Alignment

### **Primary: E-Pakistan**

NaqsKAR is **core infrastructure for e-governance**. It adds an AI intelligence layer to existing government complaint systems, directly enabling:

- ✅ **ICT services** — Complaint intake via WhatsApp, IVR, web
- ✅ **E-governance** — Automated triage and routing
- ✅ **Technology-enabled delivery** — Smart analytics and insights

### **Secondary: Equity & Empowerment**

- ✅ **Multilingual support** — 70%+ of citizens lodge complaints in Roman Urdu; NaqsKAR levels the playing field
- ✅ **Inclusive service quality** — Casual Urdu complaints get same triage as formal English
- ✅ **Marginalized group empowerment** — Lower literacy barriers to complaint filing

---

## 🗺️ Roadmap

### **Phase 1: MVP (Day 2 — May 20)**
- [x] Multilingual Normalizer API endpoint
- [x] Basic Multi-Label Classifier (3 categories)
- [x] Geo-Extractor with Pakistan gazetteer
- [x] Demo API with example complaints
- [ ] 75% backend completion for midway eval

### **Phase 2: Full Beta (Day 3 — May 21)**
- [ ] Semantic Deduplication engine + clustering
- [ ] Full urgency scoring with keyword extraction
- [ ] Analytics dashboard (heatmaps, trends)
- [ ] Suggested response templates in Urdu
- [ ] Production-ready API documentation

### **Phase 3: Pilot Integration (Post-Hackathon)**
- [ ] PCP system integration (test environment)
- [ ] WhatsApp + IVR intake modules
- [ ] Batch processing for historical complaint data
- [ ] Confidence scoring & feedback loops

### **Phase 4: Scale (6–12 months)**
- [ ] Multi-tenant SaaS platform
- [ ] Admin dashboard for government operators
- [ ] Real-time performance monitoring
- [ ] Regional customization (Punjab, Sindh, KP, Balochistan)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. **Fork** the repository
2. **Create a branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m "Add amazing feature"`)
4. **Push to your branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Code Style

We follow [PEP 8](https://pep8.org/) and use [Black](https://black.readthedocs.io/) for formatting.

```bash
# Format code
black app/

# Run linter
flake8 app/
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**Gamma Developers** — FYS 2026 AI Techathon Participants

- **Lead Developer:** Muhammad Zohaib Khan ([@ZohaibCodez](https://linkedin.com/in/zohaib-khan))
- **Contributors:** [Add team members]

---

## 📞 Contact & Support

- 📧 **Email:** [team@gamma.dev](mailto:team@gamma.dev)
- 🐛 **Report Issues:** [GitHub Issues](https://github.com/Obaid35/AITechathon-CodeNoJutsu/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Obaid35/AITechathon-CodeNoJutsu/discussions)

---

## 🙏 Acknowledgments

- **FYS 2026** for organizing the AI Techathon
- **Uraan Pakistan Initiative** for the 5 Es framework
- **Hugging Face** for pre-trained multilingual models
- **OpenAI/Anthropic** for LLM APIs
- Pakistani open-source community

---

<div align="center">

### Made with ❤️ for Pakistan's E-Governance

⭐ If you find this project useful, please give it a star!

[⬆ Back to Top](#naqskar)

</div>
