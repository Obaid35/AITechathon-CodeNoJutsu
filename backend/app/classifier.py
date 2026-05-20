"""
NaqsKAR — AI Classifier Module
Uses Groq API (Llama 3.1 8B) for multilingual complaint classification.
Handles Roman Urdu, Urdu script, English, and code-mixed text.
"""
import json
import logging
from groq import Groq
from transformers import pipeline
from app.config import settings
from app.models import ClassificationResult, Department, UrgencyLevel, Sentiment

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)

# ── Local Multilingual Transformer ─────────────────
_zero_shot_pipeline = None

def get_zero_shot_pipeline():
    """Lazy load the multilingual zero-shot classifier."""
    global _zero_shot_pipeline
    if _zero_shot_pipeline is None:
        logger.info("🧠 Loading local multilingual transformer (mDeBERTa)...")
        try:
            _zero_shot_pipeline = pipeline(
                "zero-shot-classification", 
                model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
            )
            logger.info("✅ Local transformer loaded")
        except Exception as e:
            logger.error(f"Failed to load local transformer: {e}")
    return _zero_shot_pipeline


SYSTEM_PROMPT = """You are NaqsKAR, an AI complaint triage system for Pakistan's public complaint infrastructure.

Your job: Analyze a citizen complaint (which may be in Roman Urdu, Urdu, English, or a mix) and return structured classification.

DEPARTMENTS (pick the most relevant):
- water_supply: water outage, contamination, tanker, pipeline, leakage
- electricity: load shedding, transformer, meter, billing, wiring, power outage
- gas_supply: gas pressure, leak, meter, SNGPL, SSGC, pipeline
- roads_infrastructure: potholes, broken road, street lights, footpath, bridge
- sanitation_sewerage: sewage, drainage, garbage, waste, gutter, nala
- health: hospital, clinic, medicine, doctor, ambulance, dengue, disease
- education: school, teacher, admission, fees, building condition
- police_security: theft, robbery, harassment, missing person, domestic violence, crime
- fire_emergency: fire, blast, explosion, building collapse
- public_transport: bus, metro, rickshaw, route, fare
- telecom: internet, mobile, signal, tower, PTCL, broadband
- revenue_land: property, land, patwari, registry, encroachment
- environment: pollution, smog, noise, deforestation, dumping
- general_complaint: anything not fitting above categories

URGENCY SCORING:
- critical (0.9-1.0): life-threatening — fire, medical emergency, electrocution, violence, flood, gas leak, building collapse. Keywords: marna, aag, khoon, hospital, bachao, emergency, blast, collapse
- high (0.7-0.89): serious impact — no water for days, complete power outage, sewage overflow, security threat. Keywords: bachon, beemar, 4 din se, khatarnak, banda
- medium (0.4-0.69): significant inconvenience — intermittent supply, road damage, garbage pileup
- low (0.0-0.39): minor issue — billing query, general inquiry, minor repair

RESPONSE FORMAT (strict JSON only):
{
    "department": "<department_enum>",
    "sub_category": "<specific issue in English>",
    "urgency": "<critical|high|medium|low>",
    "urgency_score": <float 0-1>,
    "sentiment": "<angry|frustrated|neutral|polite>",
    "keywords": ["keyword1", "keyword2"],
    "normalized_text": "<complaint translated/normalized to English>",
    "extracted_location": "<location mentioned in text or null>",
    "suggested_response_urdu": "<brief empathetic Urdu response acknowledging the complaint>"
}

IMPORTANT:
- Extract ANY location mentioned (sector, area, city, landmark)
- For Roman Urdu, understand the intent despite spelling variations
- Be culturally aware of Pakistani context
- Return ONLY valid JSON, no extra text
"""


async def classify_complaint(text: str) -> dict:
    """
    Classify a raw complaint text using Groq Llama 3.1.

    Args:
        text: Raw complaint in any language (Roman Urdu, Urdu, English, mixed)

    Returns:
        dict with classification results, normalized text, location, and suggested response
    """
    try:
        # --- Step 1: Local ML Transformer Prediction ---
        # This proves the product is not just an LLM wrapper
        local_predicted_dept = None
        try:
            classifier_pipeline = get_zero_shot_pipeline()
            if classifier_pipeline:
                candidate_labels = [d.value for d in Department if d.value != "general_complaint"]
                # The model understands Roman Urdu natively because of mDeBERTa
                zs_res = classifier_pipeline(text, candidate_labels)
                local_predicted_dept = zs_res["labels"][0]
                confidence = zs_res["scores"][0]
                logger.info(f"🤖 Local Transformer predicted: {local_predicted_dept} (conf: {confidence:.2f})")
        except Exception as e:
            logger.warning(f"Local Transformer prediction skipped: {e}")

        # --- Step 2: LLM Normalization & Information Extraction ---
        prompt = SYSTEM_PROMPT
        if local_predicted_dept:
            prompt += f"\n\nCRITICAL: A local ML transformer has already predicted the department as '{local_predicted_dept}'. Use this as the primary department unless strongly contraindicated."

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Classify this complaint:\n\n{text}"}
            ],
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        # Validate and normalize the department value
        dept = result.get("department", "general_complaint")
        if dept not in [d.value for d in Department]:
            dept = "general_complaint"
        result["department"] = dept

        # Validate urgency
        urgency = result.get("urgency", "medium")
        if urgency not in [u.value for u in UrgencyLevel]:
            urgency = "medium"
        result["urgency"] = urgency

        # Validate sentiment
        sentiment = result.get("sentiment", "neutral")
        if sentiment not in [s.value for s in Sentiment]:
            sentiment = "neutral"
        result["sentiment"] = sentiment

        # Ensure urgency_score is a float
        result["urgency_score"] = float(result.get("urgency_score", 0.5))

        # Ensure keywords is a list
        result["keywords"] = result.get("keywords", [])

        logger.info(f"Classified: dept={dept}, urgency={urgency}, score={result['urgency_score']}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error from Groq: {e}")
        return _fallback_classification(text)
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return _fallback_classification(text)


def _fallback_classification(text: str) -> dict:
    """
    Simple keyword-based fallback if Groq API fails.
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
        "suggested_response_urdu": "آپ کی شکایت موصول ہو گئی ہے۔ متعلقہ محکمے کو بھیج دی گئی ہے۔"
    }
