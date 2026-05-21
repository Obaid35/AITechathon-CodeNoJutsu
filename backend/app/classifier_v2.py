"""
NaqsKAR — Hybrid AI Classifier Module (v2)
Primary: Fine-tuned XLM-R (local) for department, urgency, sentiment
Secondary: Groq Llama 3.1 for normalization/translation only
Fallback: Keyword-based if both fail

Pipeline:
  1. Fine-tuned XLM-R → Department (13 labels)
  2. Fine-tuned XLM-R → Urgency (4 labels)
  3. Fine-tuned XLM-R → Sentiment (4 labels)
  4. XLM-R NER → Location extraction
  5. KeyBERT → Keyword extraction
  6. Groq Llama 3.1 → Roman Urdu → English translation + Urdu response
"""
import json
import logging
import os
from pathlib import Path

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from keybert import KeyBERT
from groq import Groq
from app.config import settings
from app.models import Department, UrgencyLevel, Sentiment

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────
MODELS_DIR = Path(__file__).parent.parent / "models"
DEPT_MODEL_DIR = MODELS_DIR / "xlmr-department" / "final"
URG_MODEL_DIR = MODELS_DIR / "xlmr-urgency" / "final"
SENT_MODEL_DIR = MODELS_DIR / "xlmr-sentiment" / "final"

# ── Groq Client (minimal usage) ───────────────
client = Groq(api_key=settings.GROQ_API_KEY)

# ── Lazy-loaded models ─────────────────────────
_dept_model = None
_dept_tokenizer = None
_dept_labels = None

_urg_model = None
_urg_tokenizer = None
_urg_labels = None

_sent_model = None
_sent_tokenizer = None
_sent_labels = None

_ner_pipeline = None
_keybert_model = None


# ── Model Loaders ──────────────────────────────
def _load_model(model_dir: Path):
    """Load a fine-tuned model + tokenizer + label map."""
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    model.eval()

    label_map_path = model_dir / "label_map.json"
    with open(label_map_path, "r") as f:
        label_map = json.load(f)
    # Convert string keys to int
    label_map = {int(k): v for k, v in label_map.items()}

    return model, tokenizer, label_map


def get_dept_model():
    global _dept_model, _dept_tokenizer, _dept_labels
    if _dept_model is None:
        logger.info("🧠 Loading fine-tuned XLM-R department model...")
        _dept_model, _dept_tokenizer, _dept_labels = _load_model(DEPT_MODEL_DIR)
        logger.info(f"✅ Department model loaded ({len(_dept_labels)} labels)")
    return _dept_model, _dept_tokenizer, _dept_labels


def get_urg_model():
    global _urg_model, _urg_tokenizer, _urg_labels
    if _urg_model is None:
        logger.info("🧠 Loading fine-tuned XLM-R urgency model...")
        _urg_model, _urg_tokenizer, _urg_labels = _load_model(URG_MODEL_DIR)
        logger.info(f"✅ Urgency model loaded ({len(_urg_labels)} labels)")
    return _urg_model, _urg_tokenizer, _urg_labels


def get_sent_model():
    global _sent_model, _sent_tokenizer, _sent_labels
    if _sent_model is None:
        logger.info("🧠 Loading fine-tuned XLM-R sentiment model...")
        _sent_model, _sent_tokenizer, _sent_labels = _load_model(SENT_MODEL_DIR)
        logger.info(f"✅ Sentiment model loaded ({len(_sent_labels)} labels)")
    return _sent_model, _sent_tokenizer, _sent_labels


def get_ner_pipeline():
    """Load XLM-R based multilingual NER for location extraction."""
    global _ner_pipeline
    if _ner_pipeline is None:
        logger.info("🧠 Loading XLM-R NER model...")
        _ner_pipeline = pipeline(
            "ner",
            model="Davlan/xlm-roberta-base-ner-hrl",
            aggregation_strategy="simple"
        )
        logger.info("✅ NER model loaded")
    return _ner_pipeline


def get_keybert():
    """Load KeyBERT for keyword extraction."""
    global _keybert_model
    if _keybert_model is None:
        logger.info("🧠 Loading KeyBERT...")
        _keybert_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
        logger.info("✅ KeyBERT loaded")
    return _keybert_model


# ── Prediction Functions ───────────────────────
def _predict(model, tokenizer, label_map, text: str) -> tuple[str, float]:
    """Run inference on a fine-tuned model. Returns (label, confidence)."""
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True,
        padding=True, max_length=128
    )
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        confidence, predicted_idx = torch.max(probs, dim=-1)

    label = label_map[predicted_idx.item()]
    return label, confidence.item()


def extract_location_ner(text: str) -> str | None:
    """Extract location entities using NER model."""
    try:
        ner = get_ner_pipeline()
        entities = ner(text)
        # Filter for LOC entities
        locations = [e["word"] for e in entities if e["entity_group"] == "LOC"]
        if locations:
            # Return the longest location (most specific)
            return max(locations, key=len)
        return None
    except Exception as e:
        logger.warning(f"NER extraction failed: {e}")
        return None


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """Extract keywords using KeyBERT."""
    try:
        kw_model = get_keybert()
        keywords = kw_model.extract_keywords(
            text, keyphrase_ngram_range=(1, 2),
            stop_words=None, top_n=top_n,
            use_mmr=True, diversity=0.5
        )
        return [kw[0] for kw in keywords]
    except Exception as e:
        logger.warning(f"KeyBERT extraction failed: {e}")
        return []


def translate_with_groq(text: str) -> dict:
    """
    Use Groq ONLY for translation + Urdu response generation.
    This is the MINIMAL Groq usage — everything else is local.
    """
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You translate Pakistani citizen complaints to English. "
                        "Input may be Roman Urdu, Urdu script, English, or code-mixed. "
                        "Return ONLY JSON with two fields:\n"
                        '{"normalized_text": "<English translation>", '
                        '"suggested_response_urdu": "<empathetic Urdu acknowledgment>"}'
                    )
                },
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "normalized_text": result.get("normalized_text", text),
            "suggested_response_urdu": result.get(
                "suggested_response_urdu",
                "آپ کی شکایت موصول ہو گئی ہے۔ متعلقہ محکمے کو بھیج دی گئی ہے۔"
            )
        }
    except Exception as e:
        logger.warning(f"Groq translation failed: {e}")
        return {
            "normalized_text": text,
            "suggested_response_urdu": "آپ کی شکایت موصول ہو گئی ہے۔ متعلقہ محکمے کو بھیج دی گئی ہے۔"
        }


# ── Urgency Score Mapping ──────────────────────
URGENCY_SCORE_MAP = {
    "critical": 0.95,
    "high": 0.78,
    "medium": 0.50,
    "low": 0.25,
}


# ── Main Classification Function ──────────────
async def classify_complaint(text: str) -> dict:
    """
    Classify a raw complaint using the hybrid pipeline.

    LOCAL models (fine-tuned XLM-R):
      - Department classification
      - Urgency classification
      - Sentiment classification
      - Location NER
      - Keyword extraction

    CLOUD (Groq — minimal):
      - Roman Urdu → English translation
      - Urdu response generation

    Args:
        text: Raw complaint in any language

    Returns:
        dict with full classification results
    """
    try:
        # ── LOCAL: Department (Fine-tuned XLM-R) ──
        dept_model, dept_tok, dept_labels = get_dept_model()
        department, dept_conf = _predict(dept_model, dept_tok, dept_labels, text)
        logger.info(f"🏛️ [LOCAL] Department: {department} (conf: {dept_conf:.2f})")

        # Validate department
        if department not in [d.value for d in Department]:
            department = "general_complaint"

        # ── LOCAL: Urgency (Fine-tuned XLM-R) ──
        urg_model, urg_tok, urg_labels = get_urg_model()
        urgency, urg_conf = _predict(urg_model, urg_tok, urg_labels, text)
        logger.info(f"🚨 [LOCAL] Urgency: {urgency} (conf: {urg_conf:.2f})")

        if urgency not in [u.value for u in UrgencyLevel]:
            urgency = "medium"

        urgency_score = URGENCY_SCORE_MAP.get(urgency, 0.5)
        # Adjust score slightly based on confidence
        urgency_score = round(urgency_score * (0.8 + 0.2 * urg_conf), 2)

        # ── LOCAL: Sentiment (Fine-tuned XLM-R) ──
        sent_model, sent_tok, sent_labels = get_sent_model()
        sentiment, sent_conf = _predict(sent_model, sent_tok, sent_labels, text)
        logger.info(f"😤 [LOCAL] Sentiment: {sentiment} (conf: {sent_conf:.2f})")

        if sentiment not in [s.value for s in Sentiment]:
            sentiment = "neutral"

        # ── LOCAL: Location NER ──
        extracted_location = extract_location_ner(text)
        logger.info(f"📍 [LOCAL] Location: {extracted_location}")

        # ── LOCAL: Keywords ──
        keywords = extract_keywords(text)
        logger.info(f"🔑 [LOCAL] Keywords: {keywords}")

        # ── CLOUD: Translation only (Groq) ──
        translation = translate_with_groq(text)
        logger.info(f"🌐 [CLOUD] Translated: {translation['normalized_text'][:60]}...")

        result = {
            "department": department,
            "sub_category": "general",  # Can be enhanced later
            "urgency": urgency,
            "urgency_score": urgency_score,
            "sentiment": sentiment,
            "keywords": keywords,
            "normalized_text": translation["normalized_text"],
            "extracted_location": extracted_location,
            "suggested_response_urdu": translation["suggested_response_urdu"],
            # Metadata for dashboard
            "model_confidence": {
                "department": round(dept_conf, 3),
                "urgency": round(urg_conf, 3),
                "sentiment": round(sent_conf, 3),
            },
            "pipeline_version": "v2-hybrid",
        }

        logger.info(
            f"✅ Classified: dept={department}, urgency={urgency}, "
            f"score={urgency_score}, sentiment={sentiment}"
        )
        return result

    except Exception as e:
        logger.error(f"Hybrid pipeline error: {e}")
        logger.info("⚠️ Falling back to keyword-based classification")
        return _fallback_classification(text)


def _fallback_classification(text: str) -> dict:
    """
    Simple keyword-based fallback if all models fail.
    """
    text_lower = text.lower()

    # Simple keyword matching for department
    dept_keywords = {
        "water_supply": ["pani", "water", "tanker", "pipeline", "leakage", "supply"],
        "electricity": ["bijli", "light", "transformer", "meter", "load shedding", "electricity", "current"],
        "gas_supply": ["gas", "sngpl", "ssgc", "pressure", "cylinder"],
        "roads_infrastructure": ["sarak", "road", "gaddha", "pothole", "street light", "footpath"],
        "sanitation_sewerage": ["gandagi", "sewage", "kachra", "garbage", "nala", "gutter", "drain"],
        "health": ["hospital", "doctor", "dawai", "medicine", "ambulance", "beemar"],
        "police_security": ["police", "chori", "theft", "harass", "missing", "violence", "dakait"],
        "fire_emergency": ["aag", "fire", "blast", "explosion", "jalaa"],
    }

    department = "general_complaint"
    for dept, keywords in dept_keywords.items():
        if any(kw in text_lower for kw in keywords):
            department = dept
            break

    # Urgency keywords
    critical_kw = ["aag", "fire", "khoon", "blood", "marna", "death", "bachao", "emergency", "blast"]
    high_kw = ["bachon", "children", "beemar", "sick", "din se", "days", "khatarnak", "dangerous"]

    urgency = "medium"
    urgency_score = 0.5
    if any(kw in text_lower for kw in critical_kw):
        urgency = "critical"
        urgency_score = 0.95
    elif any(kw in text_lower for kw in high_kw):
        urgency = "high"
        urgency_score = 0.75

    return {
        "department": department,
        "sub_category": "general",
        "urgency": urgency,
        "urgency_score": urgency_score,
        "sentiment": "neutral",
        "keywords": [],
        "normalized_text": text,
        "extracted_location": None,
        "suggested_response_urdu": "آپ کی شکایت موصول ہو گئی ہے۔ متعلقہ محکمے کو بھیج دی گئی ہے۔",
        "model_confidence": {"department": 0, "urgency": 0, "sentiment": 0},
        "pipeline_version": "v2-fallback",
    }
